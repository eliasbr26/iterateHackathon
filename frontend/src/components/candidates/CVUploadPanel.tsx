import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  User
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/services/api';

export const CVUploadPanel = () => {
  const [file, setFile] = useState<File | null>(null);
  const [candidateName, setCandidateName] = useState('');
  const [candidateEmail, setCandidateEmail] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState<{
    status: 'success' | 'error';
    message: string;
    candidateId?: number;
    parsedData?: any;
  } | null>(null);
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];

      // Validate file type
      const allowedTypes = ['.txt', '.pdf'];
      const fileExt = selectedFile.name.toLowerCase().substring(selectedFile.name.lastIndexOf('.'));

      if (!allowedTypes.includes(fileExt)) {
        toast({
          title: 'Invalid file type',
          description: `Only ${allowedTypes.join(', ')} files are supported`,
          variant: 'destructive',
        });
        return;
      }

      setFile(selectedFile);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast({
        title: 'No file selected',
        description: 'Please select a CV file to upload',
        variant: 'destructive',
      });
      return;
    }

    setUploading(true);
    setUploadProgress(0);
    setUploadResult(null);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const result = await api.uploadCandidateCV(file, {
        candidate_name: candidateName || undefined,
        candidate_email: candidateEmail || undefined,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      setUploadResult({
        status: 'success',
        message: result.message || `Successfully uploaded CV for ${result.parsed_data?.personal_info?.name || 'candidate'}`,
        candidateId: result.candidate_id,
        parsedData: result.parsed_data,
      });

      toast({
        title: 'CV Upload successful!',
        description: `Created/updated profile for ${result.parsed_data?.personal_info?.name || candidateName || 'candidate'}`,
      });

      // Reset form
      setTimeout(() => {
        setFile(null);
        setCandidateName('');
        setCandidateEmail('');
        setUploadProgress(0);
        if (document.querySelector('input[type="file"]') as HTMLInputElement) {
          (document.querySelector('input[type="file"]') as HTMLInputElement).value = '';
        }
      }, 3000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload CV';

      setUploadResult({
        status: 'error',
        message: errorMessage,
      });

      toast({
        title: 'Upload failed',
        description: errorMessage,
        variant: 'destructive',
      });
    } finally {
      setUploading(false);
    }
  };

  const clearFile = () => {
    setFile(null);
    setUploadProgress(0);
    setUploadResult(null);
    if (document.querySelector('input[type="file"]') as HTMLInputElement) {
      (document.querySelector('input[type="file"]') as HTMLInputElement).value = '';
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center gap-2">
          <User className="h-5 w-5 text-primary" />
          <CardTitle>Upload Candidate CV</CardTitle>
        </div>
        <CardDescription>
          Upload a candidate's CV to automatically create their profile (.txt, .pdf files)
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* File Upload */}
        <div className="space-y-2">
          <Label htmlFor="cv-upload">CV File</Label>
          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                id="cv-upload"
                type="file"
                accept=".txt,.pdf"
                onChange={handleFileChange}
                disabled={uploading}
                className="cursor-pointer"
              />
            </div>
            {file && !uploading && (
              <Button
                onClick={clearFile}
                variant="ghost"
                size="icon"
                className="shrink-0"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
          {file && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <FileText className="h-4 w-4" />
              <span>{file.name} ({(file.size / 1024).toFixed(2)} KB)</span>
            </div>
          )}
        </div>

        {/* Candidate Name */}
        <div className="space-y-2">
          <Label htmlFor="candidate-name">Candidate Name (Optional)</Label>
          <Input
            id="candidate-name"
            placeholder="John Doe"
            value={candidateName}
            onChange={(e) => setCandidateName(e.target.value)}
            disabled={uploading}
          />
          <p className="text-xs text-muted-foreground">
            If not provided, will be extracted from CV
          </p>
        </div>

        {/* Candidate Email */}
        <div className="space-y-2">
          <Label htmlFor="candidate-email">Candidate Email (Optional)</Label>
          <Input
            id="candidate-email"
            type="email"
            placeholder="john.doe@example.com"
            value={candidateEmail}
            onChange={(e) => setCandidateEmail(e.target.value)}
            disabled={uploading}
          />
          <p className="text-xs text-muted-foreground">
            If not provided, will be extracted from CV
          </p>
        </div>

        {/* Upload Progress */}
        {uploading && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Parsing CV and creating profile...</span>
              <span className="font-medium">{uploadProgress}%</span>
            </div>
            <Progress value={uploadProgress} className="h-2" />
          </div>
        )}

        {/* Upload Result */}
        {uploadResult && (
          <Alert variant={uploadResult.status === 'error' ? 'destructive' : 'default'}>
            {uploadResult.status === 'success' ? (
              <CheckCircle2 className="h-4 w-4" />
            ) : (
              <AlertCircle className="h-4 w-4" />
            )}
            <AlertDescription>
              {uploadResult.message}
              {uploadResult.status === 'success' && uploadResult.candidateId && (
                <div className="mt-2 text-xs">
                  <strong>Candidate ID:</strong> {uploadResult.candidateId}
                </div>
              )}
            </AlertDescription>
          </Alert>
        )}

        {/* Upload Button */}
        <Button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="w-full"
        >
          <Upload className="h-4 w-4 mr-2" />
          {uploading ? 'Processing CV...' : 'Upload CV'}
        </Button>

        {/* Help Text */}
        <p className="text-xs text-muted-foreground">
          The CV will be parsed using AI to extract skills, experience, education, and other details to automatically create or update the candidate's profile.
        </p>
      </CardContent>
    </Card>
  );
};
