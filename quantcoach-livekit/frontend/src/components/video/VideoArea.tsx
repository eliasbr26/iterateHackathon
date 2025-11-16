import { useState, memo } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Mic, MicOff, Video, VideoOff, PhoneOff, Loader2 } from 'lucide-react';
import { useLiveKit } from '@/hooks/useLiveKit';
import { api } from '@/services/api';
import { ParticipantView } from './ParticipantView';
import { useToast } from '@/hooks/use-toast';

interface VideoAreaProps {
  onRoomCreated?: (roomName: string) => void;
}

const VideoAreaComponent = ({ onRoomCreated }: VideoAreaProps) => {
  const [roomName, setRoomName] = useState('');
  const [participantName, setParticipantName] = useState('');
  const [role, setRole] = useState<'interviewer' | 'candidate'>('interviewer');
  const [isJoining, setIsJoining] = useState(false);

  const { toast } = useToast();
  const {
    room,
    isConnected,
    isConnecting,
    error,
    audioEnabled,
    videoEnabled,
    connect,
    disconnect,
    toggleAudio,
    toggleVideo,
  } = useLiveKit();

  const handleCreateRoom = async () => {
    setIsJoining(true);
    try {
      const response = await api.createRoom();
      setRoomName(response.name);

      const token = role === 'interviewer' ? response.interviewer_token : response.candidate_token;

      await connect({
        url: response.url,
        token,
      });

      // Notify parent component about room creation
      onRoomCreated?.(response.name);

      toast({
        title: 'Room Created',
        description: `Successfully created and joined room: ${response.name}`,
      });
    } catch (err) {
      console.error('Failed to create room:', err);
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to create room',
        variant: 'destructive',
      });
    } finally {
      setIsJoining(false);
    }
  };

  const handleJoinRoom = async () => {
    if (!roomName || !participantName) {
      toast({
        title: 'Missing Information',
        description: 'Please enter both room name and your name',
        variant: 'destructive',
      });
      return;
    }

    setIsJoining(true);
    try {
      const response = await api.generateToken({
        room_name: roomName,
        participant_identity: `${role}-${Date.now()}`,
        participant_name: participantName,
        role,
      });

      await connect({
        url: response.url,
        token: response.token,
      });

      toast({
        title: 'Joined Room',
        description: `Successfully joined room: ${roomName}`,
      });
    } catch (err) {
      console.error('Failed to join room:', err);
      toast({
        title: 'Error',
        description: err instanceof Error ? err.message : 'Failed to join room',
        variant: 'destructive',
      });
    } finally {
      setIsJoining(false);
    }
  };

  const handleDisconnect = async () => {
    await disconnect();
    toast({
      title: 'Disconnected',
      description: 'You have left the room',
    });
  };

  if (isConnected && room) {
    const localParticipant = room.localParticipant;
    const remoteParticipants = Array.from(room.remoteParticipants.values());

    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Live Interview Session</CardTitle>
          <CardDescription>Room: {room.name}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Video Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 min-h-[400px]">
            {/* Local Participant */}
            <div className="aspect-video">
              <ParticipantView participant={localParticipant} isLocal={true} />
            </div>

            {/* Remote Participants */}
            {remoteParticipants.map((participant) => (
              <div key={participant.sid} className="aspect-video">
                <ParticipantView participant={participant} />
              </div>
            ))}

            {/* Placeholder for waiting */}
            {remoteParticipants.length === 0 && (
              <div className="aspect-video flex items-center justify-center bg-muted rounded-lg">
                <div className="text-center text-muted-foreground">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                  <p>Waiting for other participants...</p>
                </div>
              </div>
            )}
          </div>

          {/* Controls */}
          <div className="flex items-center justify-center gap-4">
            <Button
              variant={audioEnabled ? 'default' : 'destructive'}
              size="lg"
              onClick={toggleAudio}
            >
              {audioEnabled ? <Mic className="h-5 w-5" /> : <MicOff className="h-5 w-5" />}
            </Button>
            <Button
              variant={videoEnabled ? 'default' : 'destructive'}
              size="lg"
              onClick={toggleVideo}
            >
              {videoEnabled ? <Video className="h-5 w-5" /> : <VideoOff className="h-5 w-5" />}
            </Button>
            <Button variant="destructive" size="lg" onClick={handleDisconnect}>
              <PhoneOff className="h-5 w-5" />
            </Button>
          </div>

          {error && (
            <div className="text-sm text-destructive text-center">{error}</div>
          )}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Join Interview Room</CardTitle>
        <CardDescription>Create a new room or join an existing one</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="participantName">Your Name</Label>
            <Input
              id="participantName"
              placeholder="Enter your name"
              value={participantName}
              onChange={(e) => setParticipantName(e.target.value)}
              disabled={isJoining || isConnecting}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="role">Join as</Label>
            <Select value={role} onValueChange={(value: any) => setRole(value)}>
              <SelectTrigger id="role">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="interviewer">Interviewer</SelectItem>
                <SelectItem value="candidate">Candidate</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="roomName">Room Name (optional for new room)</Label>
            <Input
              id="roomName"
              placeholder="Leave empty to create new room"
              value={roomName}
              onChange={(e) => setRoomName(e.target.value)}
              disabled={isJoining || isConnecting}
            />
          </div>
        </div>

        <div className="flex gap-4">
          <Button
            onClick={handleCreateRoom}
            disabled={isJoining || isConnecting || !participantName}
            className="flex-1"
          >
            {isJoining ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Creating...
              </>
            ) : (
              'Create New Room'
            )}
          </Button>
          <Button
            onClick={handleJoinRoom}
            disabled={isJoining || isConnecting || !roomName || !participantName}
            variant="secondary"
            className="flex-1"
          >
            {isJoining ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Joining...
              </>
            ) : (
              'Join Existing Room'
            )}
          </Button>
        </div>

        {error && (
          <div className="text-sm text-destructive text-center">{error}</div>
        )}
      </CardContent>
    </Card>
  );
};

// Wrap with memo to prevent re-renders from parent timer
export const VideoArea = memo(VideoAreaComponent);
