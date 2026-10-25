import 'package:arcane_player/llm/gemma/arcane_llm_litert.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('the default model is Gemma 4 E4B as a .litertlm download', () {
    expect(GemmaCatalog.defaultModel, GemmaCatalog.e4b);
    expect(GemmaCatalog.e4b.sizeGb, closeTo(3.4, 0.3));
    expect(GemmaCatalog.e4b.url.toString(), endsWith('.litertlm'));
  });
}
