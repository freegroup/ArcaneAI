// The public flutter_gemma chat API cannot start a conversation with an
// existing history (it glues earlier messages into the next user message).
// LiteRT-LM itself can, so this file talks to its client directly.
// ignore_for_file: implementation_imports

import 'dart:async';
import 'dart:convert';
import 'dart:math';

import 'package:arcane_player/engine/arcane_engine.dart';
import 'package:flutter_gemma/core/parsing/sdk_response_parser.dart';
import 'package:flutter_gemma/flutter_gemma.dart';
import 'package:flutter_gemma_litertlm/src/ffi/ffi_inference_model.dart';
import 'package:logging/logging.dart';

import '../llm_trace.dart';
import 'gemma_catalog.dart';

/// Every call's input and output at [Level.FINE] — the same as [LlmTrace]
/// records.
final _log = Logger('llm');

/// The on-device Gemma model as an [LlmProvider].
///
/// Every [chat] is a conversation of its own, built from the request: system
/// message, functions (native tools) and the earlier messages as real
/// user/assistant turns. Nothing is kept between calls; each call is one
/// generation. Every call is recorded in [trace].
final class GemmaLlm implements LlmProvider {
  GemmaLlm._(this._model, this.label, this.trace);

  /// Loads the active (installed) model.
  static Future<GemmaLlm> load({
    required LlmTrace trace,
    GemmaModel? model,
    PreferredBackend backend = PreferredBackend.gpu,
  }) async {
    final inference = await FlutterGemma.getActiveModel(
      maxTokens: contextTokens,
      preferredBackend: backend,
    );
    final name = (model ?? GemmaCatalog.defaultModel).label;
    return GemmaLlm._(
      inference as FfiInferenceModel,
      'LiteRT · $name · ${backend.name}',
      trace,
    );
  }

  /// Context window of a conversation, in tokens.
  static const contextTokens = 8192;

  /// Sampling of every call.
  static const _temperature = 0.3;
  static const _topK = 40;
  static const _topP = 0.95;
  static const _defaultMaxOutputTokens = 400;

  final FfiInferenceModel _model;

  /// Where every call is recorded.
  final LlmTrace trace;

  final _random = Random();
  Future<void> _running = Future.value();

  @override
  final String label;

  @override
  Future<LlmResponse> chat(
    List<LlmMessage> messages, {
    List<LlmFunction> functions = const [],
    String stage = '',
    int? maxOutputTokens,
  }) {
    // The runtime holds one conversation at a time: calls run one by one.
    final result = _running.then(
      (_) => _chat(
        messages,
        functions,
        stage,
        maxOutputTokens ?? _defaultMaxOutputTokens,
      ),
    );
    _running = result.then<void>((_) {}, onError: (_) {});
    return result;
  }

  Future<LlmResponse> _chat(
    List<LlmMessage> messages,
    List<LlmFunction> functions,
    String stage,
    int maxOutputTokens,
  ) async {
    final hasSystem = messages.first.role == LlmRole.system;
    final system = hasSystem ? messages.first.content : null;
    final turns = hasSystem ? messages.sublist(1) : messages;
    final history = turns.sublist(0, turns.length - 1);
    final message = turns.last;
    final seed = _random.nextInt(1 << 31);

    final call = LlmTraceCall(
      stage,
      settings:
          'temperature=$_temperature topK=$_topK topP=$_topP '
          'maxOutputTokens=$maxOutputTokens seed=$seed',
      messages: [
        if (system != null) LlmTraceMessage('system', system),
        for (final turn in turns) ...[
          if (turn.functionCall case final call?)
            LlmTraceMessage('assistant (funktionsaufruf)', call),
          LlmTraceMessage(turn.role.name, turn.content),
        ],
      ],
      functions: [
        for (final function in functions)
          '${function.name}: ${function.description}',
      ],
    );
    trace.start(call);
    _log.fine(
      [
        '━━━━━━━━ $stage ━━━━━━━━',
        '(${call.settings})',
        for (final message in call.messages)
          '[${message.role}]\n${message.text}',
        if (call.functions.isNotEmpty) ...[
          '[angebotene funktionen]',
          ...call.functions,
        ],
      ].join('\n'),
    );

    final watch = Stopwatch()..start();
    try {
      final conversation = await _model.ffiClient.createConversationHandle(
        systemMessage: system,
        toolsJson: functions.isEmpty
            ? null
            : jsonEncode([for (final function in functions) _tool(function)]),
        messagesJson: history.isEmpty
            ? null
            : jsonEncode([
                for (final earlier in history) ...[
                  if (earlier.functionCall case final call?) ...[
                    {
                      'role': 'assistant',
                      'tool_calls': [
                        {
                          'type': 'function',
                          'function': {
                            'name': call,
                            'arguments': <String, Object?>{},
                          },
                        },
                      ],
                    },
                    {
                      'role': 'tool',
                      'content': [
                        {
                          'type': 'tool_response',
                          'name': call,
                          'response': {'status': 'ok'},
                        },
                      ],
                    },
                  ],
                  _json(earlier),
                ],
              ]),
        temperature: _temperature,
        topK: _topK,
        topP: _topP,
        seed: seed,
        maxOutputTokens: maxOutputTokens,
      );
      final List<String> chunks;
      try {
        chunks = await conversation
            .sendMessageStreamRaw(jsonEncode(_json(message)))
            .toList();
      } finally {
        conversation.close();
      }
      final output = _output(chunks);
      trace.finish(call, watch.elapsed, output: output);
      _log.fine('◀ OUT (${watch.elapsedMilliseconds} ms)\n$output');
      return _response(chunks, functions);
    } on Object catch (e) {
      trace.finish(call, watch.elapsed, error: '$e');
      _log.fine('◀ FEHLER (${watch.elapsedMilliseconds} ms)\n$e');
      rethrow;
    }
  }

  /// Releases the model.
  Future<void> close() => _model.close();
}

/// The model's answer: the function it called and its text. Gemma sometimes
/// writes the name of a function as its first line instead of calling it.
LlmResponse _response(List<String> chunks, List<LlmFunction> functions) {
  final called = SdkResponseParser.extractToolCalls(
    chunks.join(),
  ).firstOrNull?.name;
  final content = _text(chunks);
  if (called != null) {
    return LlmResponse(content: content, functionCall: called);
  }
  final firstLine = content.split('\n').first.trim();
  if (functions.any((function) => function.name == firstLine)) {
    return LlmResponse(
      content: content
          .substring(content.indexOf(firstLine) + firstLine.length)
          .trim(),
      functionCall: firstLine,
    );
  }
  return LlmResponse(content: content);
}

/// Everything the model generated, as one text: its text, and each function
/// call as LiteRT reports it.
String _output(List<String> chunks) {
  final output = StringBuffer();
  for (final chunk in chunks) {
    if (SdkResponseParser.extractToolCalls(chunk).isNotEmpty) {
      if (output.isNotEmpty) output.writeln();
      output.writeln(chunk);
    } else {
      output.write(_text([chunk], trim: false));
    }
  }
  return output.toString().trim();
}

/// [message] as a LiteRT-LM message.
Map<String, Object?> _json(LlmMessage message) => {
  'role': message.role.name,
  'content': [
    {'type': 'text', 'text': message.content},
  ],
};

/// A function without arguments, in the format LiteRT-LM expects.
Map<String, Object?> _tool(LlmFunction function) => {
  'type': 'function',
  'function': {
    'name': function.name,
    'description': function.description,
    'parameters': {'type': 'object', 'properties': <String, Object?>{}},
  },
};

/// The text of a raw answer; every chunk is one JSON message.
String _text(List<String> chunks, {bool trim = true}) {
  final text = StringBuffer();
  for (final chunk in chunks) {
    final Object? json;
    try {
      json = jsonDecode(chunk);
    } on FormatException {
      text.write(chunk);
      continue;
    }
    if (json case {'content': final List<Object?> items}) {
      for (final item in items) {
        if (item case {'type': 'text', 'text': final String part}) {
          text.write(part);
        }
      }
    }
  }
  final result = text.toString().replaceAll(_controlTokens, '');
  return trim ? result.trim() : result;
}

/// Control tokens Gemma sometimes leaks into its text, e.g. `<|"|>`.
final _controlTokens = RegExp(r'<\|"\|>|<\|?\w+\|>');
