import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import {
  Upload,
  FileText,
  CheckCircle2,
  AlertCircle,
  X
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/services/api';

export const DocumentUploadPanel = () => {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState('company_doc');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResult, setUploadResult] = useState<{
    status: 'success' | 'error';
    message: string;
  } | null>(null);
  const { toast } = useToast();

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selectedFile = e.target.files[0];

      // Validate file type
      const allowedTypes = ['.txt', '.md', '.pdf'];
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

      // Auto-fill title from filename
      if (!title) {
        const nameWithoutExt = selectedFile.name.substring(0, selectedFile.name.lastIndexOf('.'));
        setTitle(nameWithoutExt);
      }
    }
  };

  const handleUpload = async () => {
    if (!file) {
      toast({
        title: 'No file selected',
        description: 'Please select a file to upload',
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

      const result = await api.uploadDocument(file, {
        doc_type: docType,
        title: title || undefined,
        description: description || undefined,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      setUploadResult({
        status: 'success',
        message: result.message || `Successfully uploaded ${result.chunks_indexed} chunks`,
      });

      toast({
        title: 'Upload successful!',
        description: `Indexed ${result.chunks_indexed} chunks from "${file.name}"`,
      });

      // Reset form
      setTimeout(() => {
        setFile(null);
        setTitle('');
        setDescription('');
        setUploadProgress(0);
        if (document.querySelector('input[type="file"]') as HTMLInputElement) {
          (document.querySelector('input[type="file"]') as HTMLInputElement).value = '';
        }
      }, 2000);

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to upload document';

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
          <Upload className="h-5 w-5 text-primary" />
          <CardTitle>Upload Knowledge Documents</CardTitle>
        </div>
        <CardDescription>
          Add documents to the AI knowledge base (.txt, .md, .pdf files)
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* File Upload */}
        <div className="space-y-2">
          <Label htmlFor="file-upload">Document File</Label>
          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                id="file-upload"
                type="file"
                accept=".txt,.md,.pdf"
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

        {/* Document Type */}
        <div className="space-y-2">
          <Label htmlFor="doc-type">Document Type</Label>
          <Select value={docType} onValueChange={setDocType} disabled={uploading}>
            <SelectTrigger id="doc-type">
              <SelectValue placeholder="Select document type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="company_doc">Company Document</SelectItem>
              <SelectItem value="best_practice">Best Practice</SelectItem>
              <SelectItem value="guide">Interview Guide</SelectItem>
              <SelectItem value="policy">Company Policy</SelectItem>
              <SelectItem value="knowledge">General Knowledge</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Title */}
        <div className="space-y-2">
          <Label htmlFor="title">Title (Optional)</Label>
          <Input
            id="title"
            placeholder="Document title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            disabled={uploading}
          />
        </div>

        {/* Description */}
        <div className="space-y-2">
          <Label htmlFor="description">Description (Optional)</Label>
          <Input
            id="description"
            placeholder="Brief description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={uploading}
          />
        </div>

        {/* Upload Progress */}
        {uploading && (
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Uploading and indexing...</span>
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
            <AlertDescription>{uploadResult.message}</AlertDescription>
          </Alert>
        )}

        {/* Upload Button */}
        <Button
          onClick={handleUpload}
          disabled={!file || uploading}
          className="w-full"
        >
          <Upload className="h-4 w-4 mr-2" />
          {uploading ? 'Uploading...' : 'Upload Document'}
        </Button>

        {/* Help Text */}
        <p className="text-xs text-muted-foreground">
          Uploaded documents will be chunked and indexed for the AI assistant to reference when answering questions.
        </p>
      </CardContent>
    </Card>
  );
};
