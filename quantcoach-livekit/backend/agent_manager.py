"""
Agent Manager - Manages agent lifecycle for LiveKit rooms
"""

import asyncio
import logging
from typing import Dict, Optional, Callable
from datetime import datetime
from run_audio_agent_with_evaluation import run_agent

logger = logging.getLogger(__name__)


class AgentManager:
    """Manages agent processes for different rooms"""

    def __init__(
        self,
        livekit_url: str,
        elevenlabs_api_key: str,
        anthropic_api_key: str,
        output_dir: str = "transcripts"
    ):
        self.livekit_url = livekit_url
        self.elevenlabs_api_key = elevenlabs_api_key
        self.anthropic_api_key = anthropic_api_key
        self.output_dir = output_dir

        # Track active agents: room_name -> {task, status, started_at}
        self.agents: Dict[str, dict] = {}

    async def start_agent(
        self,
        room_name: str,
        livekit_token: str,
        event_callback: Optional[Callable] = None
    ) -> bool:
        """
        Start an agent for a room

        Args:
            room_name: Name of the room
            livekit_token: Agent access token
            event_callback: Async callback for events

        Returns:
            True if agent started successfully, False otherwise
        """
        if room_name in self.agents:
            logger.warning(f"Agent already running for room: {room_name}")
            return False

        try:
            # Create agent task
            task = asyncio.create_task(
                self._run_agent_wrapper(
                    room_name=room_name,
                    livekit_token=livekit_token,
                    event_callback=event_callback
                )
            )

            # Track agent
            self.agents[room_name] = {
                "task": task,
                "status": "running",
                "started_at": datetime.now().isoformat(),
                "error": None
            }

            logger.info(f"✅ Started agent for room: {room_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to start agent for room {room_name}: {e}")
            return False

    async def _run_agent_wrapper(
        self,
        room_name: str,
        livekit_token: str,
        event_callback: Optional[Callable]
    ):
        """Wrapper to run agent and handle errors"""
        try:
            await run_agent(
                room_name=room_name,
                livekit_url=self.livekit_url,
                livekit_token=livekit_token,
                elevenlabs_api_key=self.elevenlabs_api_key,
                anthropic_api_key=self.anthropic_api_key,
                event_callback=event_callback,
                output_dir=self.output_dir
            )

            # Update status on completion
            if room_name in self.agents:
                self.agents[room_name]["status"] = "completed"

        except Exception as e:
            logger.error(f"❌ Agent error for room {room_name}: {e}", exc_info=True)

            # Update status on error
            if room_name in self.agents:
                self.agents[room_name]["status"] = "error"
                self.agents[room_name]["error"] = str(e)

            # Send error event
            if event_callback:
                try:
                    await event_callback({
                        "type": "error",
                        "data": {
                            "room": room_name,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat()
                        }
                    })
                except Exception:
                    pass

    async def stop_agent(self, room_name: str) -> bool:
        """
        Stop an agent for a room

        Args:
            room_name: Name of the room

        Returns:
            True if agent stopped successfully, False otherwise
        """
        if room_name not in self.agents:
            logger.warning(f"No agent running for room: {room_name}")
            return False

        try:
            agent_info = self.agents[room_name]
            task = agent_info["task"]

            # Cancel the task
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"✅ Stopped agent for room: {room_name}")

            # Update status
            agent_info["status"] = "stopped"

            return True

        except Exception as e:
            logger.error(f"❌ Failed to stop agent for room {room_name}: {e}")
            return False

    def get_agent_status(self, room_name: str) -> Optional[dict]:
        """
        Get status of an agent

        Args:
            room_name: Name of the room

        Returns:
            Agent status dict or None if not found
        """
        if room_name not in self.agents:
            return None

        agent_info = self.agents[room_name]
        return {
            "status": agent_info["status"],
            "started_at": agent_info["started_at"],
            "error": agent_info.get("error")
        }

    def list_active_agents(self) -> Dict[str, dict]:
        """List all active agents"""
        return {
            room: {
                "status": info["status"],
                "started_at": info["started_at"],
                "error": info.get("error")
            }
            for room, info in self.agents.items()
            if info["status"] in ["running", "starting"]
        }

    async def cleanup(self):
        """Stop all agents"""
        logger.info("🧹 Cleaning up all agents...")

        for room_name in list(self.agents.keys()):
            await self.stop_agent(room_name)

        self.agents.clear()
        logger.info("✅ All agents stopped")
