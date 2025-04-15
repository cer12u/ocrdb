import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Loader2, Upload } from 'lucide-react';
import { documentApi } from '@/lib/api';
import { OCREngine, systemApi } from '@/lib/api';
import { useToast } from '../hooks/use-toast';

export function UploadForm({ onUploadComplete }: { onUploadComplete?: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [tags, setTags] = useState('');
  const [folderPath, setFolderPath] = useState('/');
  const [ocrEngine, setOcrEngine] = useState<string>('');
  const [isUploading, setIsUploading] = useState(false);
  const [ocrEngines, setOcrEngines] = useState<OCREngine[]>([]);
  const [isLoadingEngines, setIsLoadingEngines] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    const loadOCREngines = async () => {
      setIsLoadingEngines(true);
      try {
        const engines = await systemApi.getOCREngines();
        setOcrEngines(engines.filter(engine => engine.available));
        
        if (engines.length > 0) {
          const defaultEngine = engines.find(e => e.available);
          if (defaultEngine) {
            setOcrEngine(defaultEngine.id);
          }
        }
      } catch (error) {
        console.error('Failed to load OCR engines:', error);
        toast({
          title: 'Error',
          description: 'Failed to load OCR engines',
          variant: 'destructive',
        });
      } finally {
        setIsLoadingEngines(false);
      }
    };
    
    loadOCREngines();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!file) {
      toast({
        title: 'Error',
        description: 'Please select a file to upload',
        variant: 'destructive',
      });
      return;
    }
    
    setIsUploading(true);
    
    try {
      const tagList = tags.split(',').map(tag => tag.trim()).filter(tag => tag);
      await documentApi.uploadDocument(file, tagList, folderPath, ocrEngine || undefined);
      
      toast({
        title: 'Success',
        description: 'Document uploaded successfully',
      });
      
      setFile(null);
      setTags('');
      
      if (onUploadComplete) {
        onUploadComplete();
      }
    } catch (error) {
      console.error('Upload error:', error);
      toast({
        title: 'Upload Failed',
        description: error instanceof Error ? error.message : 'Failed to upload document',
        variant: 'destructive',
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <Card className="w-full max-w-md">
      <CardHeader>
        <CardTitle>Upload Document</CardTitle>
        <CardDescription>
          Upload an image, PDF, or ZIP file for OCR processing
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="file">File</Label>
            <Input
              id="file"
              type="file"
              onChange={handleFileChange}
              accept="image/*,.pdf,.zip"
              disabled={isUploading}
            />
            {file && (
              <p className="text-sm text-muted-foreground">
                Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
              </p>
            )}
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="tags">Tags (comma separated)</Label>
            <Input
              id="tags"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="tag1, tag2, tag3"
              disabled={isUploading}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="folder">Folder Path</Label>
            <Input
              id="folder"
              value={folderPath}
              onChange={(e) => setFolderPath(e.target.value)}
              placeholder="/"
              disabled={isUploading}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="ocr-engine">OCR Engine</Label>
            <Select
              value={ocrEngine}
              onValueChange={setOcrEngine}
              disabled={isUploading || isLoadingEngines || ocrEngines.length === 0}
            >
              <SelectTrigger id="ocr-engine">
                <SelectValue placeholder="Select OCR engine" />
              </SelectTrigger>
              <SelectContent>
                {isLoadingEngines ? (
                  <SelectItem value="loading" disabled>
                    Loading engines...
                  </SelectItem>
                ) : ocrEngines.length === 0 ? (
                  <SelectItem value="none" disabled>
                    No engines available
                  </SelectItem>
                ) : (
                  ocrEngines.map((engine) => (
                    <SelectItem key={engine.id} value={engine.id}>
                      {engine.name} {engine.version ? `(${engine.version})` : ''}
                    </SelectItem>
                  ))
                )}
              </SelectContent>
            </Select>
          </div>
          
          <Button type="submit" className="w-full" disabled={isUploading || !file}>
            {isUploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload
              </>
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
