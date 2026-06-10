"""
Telegram runner — Telegram Bot for playing ArcaneAI via chat.

Setup:
    1. Create a bot via @BotFather and get the token
    2. Set TELEGRAM_BOT_TOKEN in environment or config.yaml
    3. Optionally set STT enabled: true in config.yaml for voice input

Commands:
    /start  — Start or restart the game
    /reset  — Reset game to beginning
    /status — Show current state and inventory
"""
from __future__ import annotations
import asyncio
import logging
import os
from typing import Dict, Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from .base import BaseRunner
from session import GameSession
from session_store import SessionStore
from config_loader import load_config
from messaging.telegram_queue import TelegramMessageQueue
from audio.null_sink import NullSink
from sound.null_jukebox import NullJukebox

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramRunner(BaseRunner):
    """Runs the game as a Telegram bot."""

    def __init__(self) -> None:
        self.config = load_config()
        self.store = SessionStore()
        self.sessions: Dict[int, GameSession] = {}  # in-memory cache

    # ── Session management ──────────────────────────────────────────────

    def _create_session(self, chat_id: int) -> GameSession:
        session = GameSession(
            session_id=str(chat_id),
            config=self.config,
            message_queue=TelegramMessageQueue(),
            audio_sink=NullSink(),
            jukebox=NullJukebox(),
        )
        self.sessions[chat_id] = session
        return session

    def _get_or_create_session(self, chat_id: int) -> GameSession:
        if chat_id in self.sessions:
            return self.sessions[chat_id]

        session = self._create_session(chat_id)

        # Restore persisted state if available
        saved = self.store.load(chat_id)
        if saved:
            try:
                session.restore_from_dict(saved)
                logger.info(f"[{chat_id}] Session restored from disk")
            except Exception as e:
                logger.warning(f"[{chat_id}] Could not restore session: {e}")

        return session

    async def _recover_pending(self, update: Update, session: GameSession) -> None:
        """
        If the server restarted before a response was sent, recover it now.

        Two cases:
        - History already has the entry (process_input ran, send crashed)
          → re-send the stored assistant response, no LLM call needed
        - History has no entry (crash before process_input)
          → re-process the input now
        """
        chat_id = update.effective_chat.id
        pending = self.store.load_pending(chat_id)
        if not pending:
            return

        logger.info(f"[{chat_id}] Recovering pending input: {pending!r}")
        entries = session.game_engine.controller.history.entries

        if entries and entries[-1].user_input == pending:
            # Already processed — just re-send the stored response
            logger.info(f"[{chat_id}] Pending already in history, re-sending response")
            await self._send_response(update, session, entries[-1].llm_response)
        else:
            # Never processed — run it through the engine now
            logger.info(f"[{chat_id}] Pending not in history, re-processing")
            result = session.game_engine.process_input(pending)
            await self._send_response(update, session, result.get("response", ""))

        self.store.clear_pending(chat_id)

    def _save_session(self, chat_id: int, session: GameSession) -> None:
        try:
            self.store.save(chat_id, session.to_dict())
        except Exception as e:
            logger.warning(f"[{chat_id}] Could not save session: {e}")

    def _reset_session(self, chat_id: int) -> GameSession:
        self.store.delete(chat_id)
        self.sessions.pop(chat_id, None)
        return self._create_session(chat_id)

    # ── Message sending ─────────────────────────────────────────────────

    def _build_status_block(self, session: GameSession) -> str:
        """Build a compact status block shown after each response."""
        state = session.game_engine.state_engine.get_current_state().name
        inv = session.game_engine.inventory.to_dict()
        inv_lines = "\n".join(
            f"  🎒 {k}: {v}" for k, v in sorted(inv.items()) if v not in (False, 0, "")
        ) or "  🎒 —"
        return f"<i>📍 {state}\n{inv_lines}</i>"

    async def _send_to_chat(self, bot, chat_id: int, session: GameSession, text: str) -> None:
        """Send a message directly to a chat_id (no Update object needed)."""
        if not text:
            return
        status = self._build_status_block(session)
        try:
            await bot.send_message(chat_id, f"{text}\n\n{status}", parse_mode="HTML")
        except Exception:
            import re
            await bot.send_message(chat_id, re.sub(r'<[^>]+>', '', text))
        self._save_session(chat_id, session)

    async def _signal_action(self, update: Update) -> None:
        """React to the user's message with ⚡ to signal a game action was executed."""
        try:
            from telegram import ReactionTypeEmoji
            await update.message.set_reaction([ReactionTypeEmoji("👍")])
        except Exception:
            pass  # Reactions not supported in this chat type — silently skip

    async def _send_response(
        self,
        update: Update,
        session: GameSession,
        text: str,
    ) -> None:
        """Send game response and flush any queued game messages."""
        chat_id = update.effective_chat.id
        queue: TelegramMessageQueue = session.message_queue

        # Send main narrative response with status spoiler appended
        if text:
            status = self._build_status_block(session)
            await update.message.reply_text(
                f"{text}\n\n{status}",
                parse_mode="HTML",
            )

        # Send any additional queued messages (inventory updates, state changes)
        for msg in queue.flush():
            if msg["type"] == "inventory_update":
                pass  # silently ignore for now
            elif msg["type"] == "state_change":
                pass  # silently ignore for now

        self._save_session(chat_id, session)

    # ── Handlers ────────────────────────────────────────────────────────

    async def handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """/start — (re)start the game and show help."""
        chat_id = update.effective_chat.id
        session = self._reset_session(chat_id)
        intro = session.game_engine.start_game()
        await self._send_response(update, session, intro)
        help_text = session.game_engine.game_data.get('help_text', '')
        if help_text:
            try:
                await update.message.reply_text(help_text, parse_mode="HTML")
            except Exception:
                import re
                await update.message.reply_text(re.sub(r'<[^>]+>', '', help_text))

    async def handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """/help — show game help text from config."""
        try:
            chat_id = update.effective_chat.id
            session = self._get_or_create_session(chat_id)
            help_text = session.game_engine.game_data.get('help_text', '')
            if not help_text:
                help_text = "Kein Hilfetext konfiguriert."
            try:
                await update.message.reply_text(help_text, parse_mode="HTML")
            except Exception:
                import re
                await update.message.reply_text(re.sub(r'<[^>]+>', '', help_text))
        except Exception as e:
            logger.error(f"handle_help failed: {e}", exc_info=True)
            await update.message.reply_text("❌ Fehler beim Laden des Hilfetexts.")

    async def handle_reset(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """/reset — same as /start."""
        await self.handle_start(update, context)

    async def handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """/status — show current state and key inventory items."""
        chat_id = update.effective_chat.id
        session = self._get_or_create_session(chat_id)
        state = session.game_engine.state_engine.get_current_state().name
        inv = session.game_engine.inventory.to_dict()
        inv_text = "\n".join(
            f"  {k}: {v}" for k, v in sorted(inv.items()) if v not in (False, 0, "")
        ) or "  (leer)"
        await update.message.reply_text(f"📍 State: {state}\n\n🎒 Inventar:\n{inv_text}")

    def _is_new_session(self, session: GameSession) -> bool:
        """True if the game hasn't been started yet (no history, no state progression)."""
        return len(session.game_engine.controller.history.entries) == 0

    async def _ensure_started(self, update: Update, session: GameSession) -> None:
        """If the session is fresh, run start_game() and send the intro first."""
        if self._is_new_session(session):
            intro = session.game_engine.start_game()
            if intro:
                await update.message.reply_text(intro)

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle plain text messages."""
        chat_id = update.effective_chat.id
        text = update.message.text.strip()
        if not text:
            return

        session = self._get_or_create_session(chat_id)
        session.update_activity()

        await self._recover_pending(update, session)
        await self._ensure_started(update, session)

        self.store.save_pending(chat_id, text)
        result = session.game_engine.process_input(text)
        if result.get("executed_action"):
            await self._signal_action(update)
        await self._send_response(update, session, result.get("response", ""))
        await self._send_game_target_reminder(update, session)
        self.store.clear_pending(chat_id)

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle voice messages via STT."""
        from stt import STTFactory

        stt_factory = STTFactory()
        stt = stt_factory.create_provider()

        # Download voice file from Telegram
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        audio_bytes = bytes(await voice_file.download_as_bytearray())

        text = stt.transcribe(audio_bytes, mime_type="audio/ogg")
        if not text:
            await update.message.reply_text("❓ Ich konnte dich nicht verstehen. Bitte nochmal versuchen.")
            return

        # Echo transcription so user knows what was understood
        await update.message.reply_text(f"🎤 {text}")

        # Process as regular text input
        chat_id = update.effective_chat.id
        session = self._get_or_create_session(chat_id)
        session.update_activity()

        await self._recover_pending(update, session)
        await self._ensure_started(update, session)

        self.store.save_pending(chat_id, text)
        result = session.game_engine.process_input(text)
        if result.get("executed_action"):
            await self._signal_action(update)
        await self._send_response(update, session, result.get("response", ""))
        await self._send_game_target_reminder(update, session)
        self.store.clear_pending(chat_id)

    async def _send_game_target_reminder(self, update: Update, session: GameSession) -> None:
        """Send a standalone game target reminder if the player has lost focus."""
        reminder = session.game_engine.controller.get_game_target_reminder()
        if reminder:
            await update.message.reply_text(f"💡 {reminder}")

    # ── Entry point ──────────────────────────────────────────────────────

    async def _startup_recovery(self, app) -> None:
        """On startup: find all sessions with a pending unanswered input and send the response."""
        pending_files = list(self.store.sessions_dir.glob("*_pending.txt"))
        if not pending_files:
            return
        logger.info(f"[startup] Found {len(pending_files)} pending session(s) to recover")
        for pending_path in pending_files:
            chat_id = int(pending_path.stem.replace("_pending", ""))
            pending = self.store.load_pending(chat_id)
            if not pending:
                continue
            try:
                session = self._get_or_create_session(chat_id)
                entries = session.game_engine.controller.history.entries
                if entries and entries[-1].user_input == pending:
                    response = entries[-1].llm_response
                    logger.info(f"[startup] [{chat_id}] Re-sending stored response for: {pending!r}")
                else:
                    logger.info(f"[startup] [{chat_id}] Re-processing: {pending!r}")
                    result = session.game_engine.process_input(pending)
                    response = result.get("response", "")
                if response:
                    await self._send_to_chat(app.bot, chat_id, session, response)
                self.store.clear_pending(chat_id)
            except Exception as e:
                logger.error(f"[startup] [{chat_id}] Recovery failed: {e}", exc_info=True)

    def run(self) -> None:
        token = (
            self.config.get("telegram", {}).get("bot_token")
            or os.environ.get("TELEGRAM_BOT_TOKEN")
        )
        if not token:
            raise ValueError(
                "Telegram bot token not found. "
                "Set TELEGRAM_BOT_TOKEN env var or telegram.bot_token in config.yaml."
            )

        app = Application.builder().token(token).post_init(self._startup_recovery).build()

        async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
            logger.error("Unhandled exception in handler", exc_info=context.error)

        app.add_error_handler(error_handler)
        app.add_handler(CommandHandler("start", self.handle_start))
        app.add_handler(CommandHandler("reset", self.handle_reset))
        app.add_handler(CommandHandler("help", self.handle_help))
        app.add_handler(CommandHandler("status", self.handle_status))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))

        logger.info("Telegram bot starting...")
        app.run_polling()
