import { useState, useEffect } from 'react';
import { Document, documentApi } from '@/lib/api';
import { Card } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Loader2, FileText, Image, File, Download, RefreshCw, Trash2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { OCRStatus, searchApi } from '@/lib/api';

export function DocumentList({ 
  folderPath, 
  searchQuery,
  refreshTrigger = 0
}: { 
  folderPath?: string;
  searchQuery?: string;
  refreshTrigger?: number;
}) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    const loadDocuments = async () => {
      setIsLoading(true);
      try {
        if (searchQuery) {
          const results = await searchApi.searchDocuments(searchQuery);
          setDocuments(results);
        } else {
          const docs = await documentApi.listDocuments(0, 100, folderPath);
          setDocuments(docs);
        }
      } catch (error) {
        console.error('Failed to load documents:', error);
        toast({
          title: 'Error',
          description: 'Failed to load documents',
          variant: 'destructive',
        });
      } finally {
        setIsLoading(false);
      }
    };

    loadDocuments();
  }, [folderPath, searchQuery, refreshTrigger]);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this document?')) {
      return;
    }

    try {
      await documentApi.deleteDocument(id);
      setDocuments(documents.filter(doc => doc.id !== id));
      toast({
        title: 'Success',
        description: 'Document deleted successfully',
      });
    } catch (error) {
      console.error('Failed to delete document:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete document',
        variant: 'destructive',
      });
    }
  };

  const handleReprocessOCR = async (id: string) => {
    try {
      await documentApi.reprocessOCR(id);
      toast({
        title: 'Success',
        description: 'OCR processing started',
      });
      
      setDocuments(documents.map(doc => 
        doc.id === id 
          ? { ...doc, ocr_status: OCRStatus.PROCESSING } 
          : doc
      ));
    } catch (error) {
      console.error('Failed to reprocess OCR:', error);
      toast({
        title: 'Error',
        description: 'Failed to reprocess OCR',
        variant: 'destructive',
      });
    }
  };

  const getDocumentIcon = (mimeType: string) => {
    if (mimeType.startsWith('image/')) {
      return <Image className="h-6 w-6" />;
    } else if (mimeType === 'application/pdf') {
      return <FileText className="h-6 w-6" />;
    } else {
      return <File className="h-6 w-6" />;
    }
  };

  const getStatusBadge = (status: OCRStatus) => {
    switch (status) {
      case OCRStatus.PENDING:
        return <Badge variant="outline">Pending</Badge>;
      case OCRStatus.PROCESSING:
        return <Badge variant="secondary">Processing</Badge>;
      case OCRStatus.COMPLETED:
        return <Badge variant="default">Completed</Badge>;
      case OCRStatus.FAILED:
        return <Badge variant="destructive">Failed</Badge>;
      default:
        return null;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) {
      return `${bytes} B`;
    } else if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(2)} KB`;
    } else {
      return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center p-8">
        <p className="text-muted-foreground">No documents found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {documents.map((doc) => (
        <Card key={doc.id} className="overflow-hidden">
          <div className="flex">
            {doc.thumbnail_path ? (
              <div className="w-24 h-24 flex-shrink-0">
                <img 
                  src={documentApi.getThumbnailUrl(doc.id)} 
                  alt={doc.filename}
                  className="w-full h-full object-cover"
                />
              </div>
            ) : (
              <div className="w-24 h-24 flex-shrink-0 bg-muted flex items-center justify-center">
                {getDocumentIcon(doc.mime_type)}
              </div>
            )}
            
            <div className="flex-grow p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium">{doc.filename}</h3>
                  <div className="text-sm text-muted-foreground">
                    {formatFileSize(doc.size)} • {new Date(doc.upload_date).toLocaleString()}
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {getStatusBadge(doc.ocr_status)}
                    {doc.tags.map((tag) => (
                      <Badge 
                        key={tag.id} 
                        style={{ backgroundColor: tag.color, color: '#fff' }}
                      >
                        {tag.name}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                <div className="flex space-x-2">
                  <Button 
                    variant="outline" 
                    size="icon"
                    onClick={() => window.open(documentApi.getOriginalFileUrl(doc.id))}
                    title="Download original"
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    size="icon"
                    onClick={() => handleReprocessOCR(doc.id)}
                    disabled={doc.ocr_status === OCRStatus.PROCESSING}
                    title="Reprocess OCR"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    size="icon"
                    onClick={() => handleDelete(doc.id)}
                    title="Delete document"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                  
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button 
                        variant="default" 
                        size="sm"
                        onClick={() => setSelectedDocument(doc)}
                      >
                        View
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
                      {selectedDocument && (
                        <>
                          <DialogHeader>
                            <DialogTitle>{selectedDocument.filename}</DialogTitle>
                            <DialogDescription>
                              {new Date(selectedDocument.upload_date).toLocaleString()} • 
                              {selectedDocument.ocr_engine && ` OCR: ${selectedDocument.ocr_engine}`}
                            </DialogDescription>
                          </DialogHeader>
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                            <div>
                              <h4 className="font-medium mb-2">Preview</h4>
                              {selectedDocument.thumbnail_path ? (
                                <img 
                                  src={documentApi.getThumbnailUrl(selectedDocument.id)} 
                                  alt={selectedDocument.filename}
                                  className="max-w-full rounded border"
                                />
                              ) : (
                                <div className="w-full h-48 bg-muted flex items-center justify-center rounded border">
                                  {getDocumentIcon(selectedDocument.mime_type)}
                                </div>
                              )}
                              
                              <div className="mt-4 flex justify-between">
                                <Button 
                                  variant="outline"
                                  onClick={() => window.open(documentApi.getOriginalFileUrl(selectedDocument.id))}
                                >
                                  <Download className="h-4 w-4 mr-2" />
                                  Download Original
                                </Button>
                                
                                <Button 
                                  variant="outline"
                                  onClick={() => handleReprocessOCR(selectedDocument.id)}
                                  disabled={selectedDocument.ocr_status === OCRStatus.PROCESSING}
                                >
                                  <RefreshCw className="h-4 w-4 mr-2" />
                                  Reprocess OCR
                                </Button>
                              </div>
                            </div>
                            
                            <div>
                              <h4 className="font-medium mb-2">OCR Text</h4>
                              {selectedDocument.ocr_status === OCRStatus.COMPLETED ? (
                                <div className="bg-muted p-4 rounded border h-[300px] overflow-y-auto">
                                  <pre className="whitespace-pre-wrap text-sm">
                                    {selectedDocument.ocr_text || 'No text extracted'}
                                  </pre>
                                </div>
                              ) : (
                                <div className="bg-muted p-4 rounded border h-[300px] flex items-center justify-center">
                                  {selectedDocument.ocr_status === OCRStatus.PROCESSING ? (
                                    <div className="text-center">
                                      <Loader2 className="h-8 w-8 animate-spin mx-auto mb-2" />
                                      <p>Processing OCR...</p>
                                    </div>
                                  ) : selectedDocument.ocr_status === OCRStatus.FAILED ? (
                                    <p className="text-destructive">OCR processing failed</p>
                                  ) : (
                                    <p>Waiting for OCR processing</p>
                                  )}
                                </div>
                              )}
                              
                              <div className="mt-4">
                                <h4 className="font-medium mb-2">Details</h4>
                                <dl className="grid grid-cols-2 gap-2 text-sm">
                                  <dt className="text-muted-foreground">Size:</dt>
                                  <dd>{formatFileSize(selectedDocument.size)}</dd>
                                  
                                  <dt className="text-muted-foreground">Type:</dt>
                                  <dd>{selectedDocument.mime_type}</dd>
                                  
                                  <dt className="text-muted-foreground">Folder:</dt>
                                  <dd>{selectedDocument.folder_path}</dd>
                                  
                                  <dt className="text-muted-foreground">OCR Status:</dt>
                                  <dd>{selectedDocument.ocr_status}</dd>
                                  
                                  {selectedDocument.ocr_engine && (
                                    <>
                                      <dt className="text-muted-foreground">OCR Engine:</dt>
                                      <dd>{selectedDocument.ocr_engine} {selectedDocument.ocr_engine_version}</dd>
                                    </>
                                  )}
                                </dl>
                              </div>
                            </div>
                          </div>
                        </>
                      )}
                    </DialogContent>
                  </Dialog>
                </div>
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
