/**
 * API client for the OCR database backend
 */

const API_BASE_URL = 'http://localhost:8000/api';

export interface Tag {
  id: string;
  name: string;
  color: string;
}

export enum OCRStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed"
}

export interface Document {
  id: string;
  filename: string;
  mime_type: string;
  size: number;
  folder_path: string;
  file_path: string;
  thumbnail_path?: string;
  upload_date: string;
  ocr_status: OCRStatus;
  ocr_text?: string;
  ocr_engine?: string;
  ocr_engine_version?: string;
  tags: Tag[];
  metadata: Record<string, any>;
}

export interface SearchQuery {
  text?: string;
  tags?: string[];
  folder_path?: string;
  mime_types?: string[];
  date_from?: string;
  date_to?: string;
  page: number;
  page_size: number;
  sort_by: string;
  sort_order: string;
}

export interface SystemSettings {
  storage_type: string;
  s3_endpoint?: string;
  s3_bucket?: string;
  s3_access_key?: string;
  s3_secret_key?: string;
  max_file_size: number;
  max_zip_size: number;
  default_ocr_engine: string;
}

export interface StorageInfo {
  total_documents: number;
  total_size: number;
  storage_type: string;
  storage_location: string;
}

export interface OCREngine {
  id: string;
  name: string;
  version: string;
  available: boolean;
}

export interface Folder {
  path: string;
  name: string;
  document_count: number;
}

/**
 * Document API
 */
export const documentApi = {
  /**
   * Upload a document
   */
  uploadDocument: async (
    file: File,
    tags: string[] = [],
    folderPath: string = "/",
    ocrEngine?: string
  ): Promise<Document> => {
    const formData = new FormData();
    formData.append('file', file);
    
    if (tags.length > 0) {
      formData.append('tags', tags.join(','));
    }
    
    formData.append('folder_path', folderPath);
    
    if (ocrEngine) {
      formData.append('ocr_engine', ocrEngine);
    }
    
    const response = await fetch(`${API_BASE_URL}/documents`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to upload document');
    }
    
    return response.json();
  },
  
  /**
   * List documents
   */
  listDocuments: async (
    skip: number = 0,
    limit: number = 100,
    folderPath?: string
  ): Promise<Document[]> => {
    let url = `${API_BASE_URL}/documents?skip=${skip}&limit=${limit}`;
    
    if (folderPath) {
      url += `&folder_path=${encodeURIComponent(folderPath)}`;
    }
    
    const response = await fetch(url);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list documents');
    }
    
    return response.json();
  },
  
  /**
   * Get a document
   */
  getDocument: async (id: string): Promise<Document> => {
    const response = await fetch(`${API_BASE_URL}/documents/${id}`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get document');
    }
    
    return response.json();
  },
  
  /**
   * Delete a document
   */
  deleteDocument: async (id: string): Promise<boolean> => {
    const response = await fetch(`${API_BASE_URL}/documents/${id}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete document');
    }
    
    const result = await response.json();
    return result.success;
  },
  
  /**
   * Get the original file URL for a document
   */
  getOriginalFileUrl: (id: string): string => {
    return `${API_BASE_URL}/documents/${id}/original`;
  },
  
  /**
   * Get the thumbnail URL for a document
   */
  getThumbnailUrl: (id: string): string => {
    return `${API_BASE_URL}/documents/${id}/thumbnail`;
  },
  
  /**
   * Re-process a document with OCR
   */
  reprocessOCR: async (id: string, ocrEngine?: string): Promise<void> => {
    let url = `${API_BASE_URL}/documents/${id}/reocr`;
    
    if (ocrEngine) {
      url += `?ocr_engine=${encodeURIComponent(ocrEngine)}`;
    }
    
    const response = await fetch(url, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to reprocess OCR');
    }
  },
};

/**
 * Search API
 */
export const searchApi = {
  /**
   * Search documents
   */
  searchDocuments: async (
    query?: string,
    tags?: string[],
    folderPath?: string,
    mimeTypes?: string[],
    dateFrom?: Date,
    dateTo?: Date,
    page: number = 1,
    pageSize: number = 20,
    sortBy: string = 'upload_date',
    sortOrder: string = 'desc'
  ): Promise<Document[]> => {
    let url = `${API_BASE_URL}/search?page=${page}&page_size=${pageSize}&sort_by=${sortBy}&sort_order=${sortOrder}`;
    
    if (query) {
      url += `&q=${encodeURIComponent(query)}`;
    }
    
    if (tags && tags.length > 0) {
      url += `&tags=${encodeURIComponent(tags.join(','))}`;
    }
    
    if (folderPath) {
      url += `&folder_path=${encodeURIComponent(folderPath)}`;
    }
    
    if (mimeTypes && mimeTypes.length > 0) {
      url += `&mime_types=${encodeURIComponent(mimeTypes.join(','))}`;
    }
    
    if (dateFrom) {
      url += `&date_from=${dateFrom.toISOString()}`;
    }
    
    if (dateTo) {
      url += `&date_to=${dateTo.toISOString()}`;
    }
    
    const response = await fetch(url);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to search documents');
    }
    
    return response.json();
  },
  
  /**
   * Advanced search
   */
  advancedSearch: async (query: SearchQuery): Promise<Document[]> => {
    const response = await fetch(`${API_BASE_URL}/search/advanced`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(query),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to search documents');
    }
    
    return response.json();
  },
};

/**
 * Folder API
 */
export const folderApi = {
  /**
   * List folders
   */
  listFolders: async (): Promise<Folder[]> => {
    const response = await fetch(`${API_BASE_URL}/folders`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list folders');
    }
    
    return response.json();
  },
  
  /**
   * Create a folder
   */
  createFolder: async (path: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/folders?path=${encodeURIComponent(path)}`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create folder');
    }
  },
  
  /**
   * Get folder contents
   */
  getFolderContents: async (
    path: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<{ path: string; name: string; documents: Document[] }> => {
    const response = await fetch(
      `${API_BASE_URL}/folders/${encodeURIComponent(path)}?skip=${skip}&limit=${limit}`
    );
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get folder contents');
    }
    
    return response.json();
  },
};

/**
 * Tag API
 */
export const tagApi = {
  /**
   * Create a tag
   */
  createTag: async (name: string, color: string = '#808080'): Promise<Tag> => {
    const response = await fetch(`${API_BASE_URL}/tags`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ name, color }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create tag');
    }
    
    return response.json();
  },
  
  /**
   * List tags
   */
  listTags: async (): Promise<Tag[]> => {
    const response = await fetch(`${API_BASE_URL}/tags`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to list tags');
    }
    
    return response.json();
  },
  
  /**
   * Update a tag
   */
  updateTag: async (
    id: string,
    name?: string,
    color?: string
  ): Promise<Tag> => {
    let url = `${API_BASE_URL}/tags/${id}?`;
    
    if (name) {
      url += `name=${encodeURIComponent(name)}&`;
    }
    
    if (color) {
      url += `color=${encodeURIComponent(color)}`;
    }
    
    const response = await fetch(url, {
      method: 'PUT',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update tag');
    }
    
    return response.json();
  },
  
  /**
   * Delete a tag
   */
  deleteTag: async (id: string): Promise<boolean> => {
    const response = await fetch(`${API_BASE_URL}/tags/${id}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete tag');
    }
    
    const result = await response.json();
    return result.success;
  },
  
  /**
   * Add a tag to a document
   */
  addTagToDocument: async (documentId: string, tagId: string): Promise<Document> => {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/tags/${tagId}`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to add tag to document');
    }
    
    return response.json();
  },
  
  /**
   * Remove a tag from a document
   */
  removeTagFromDocument: async (documentId: string, tagId: string): Promise<Document> => {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/tags/${tagId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to remove tag from document');
    }
    
    return response.json();
  },
};

/**
 * System API
 */
export const systemApi = {
  /**
   * Get storage info
   */
  getStorageInfo: async (): Promise<StorageInfo> => {
    const response = await fetch(`${API_BASE_URL}/system/storage`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get storage info');
    }
    
    return response.json();
  },
  
  /**
   * Get OCR engines
   */
  getOCREngines: async (): Promise<OCREngine[]> => {
    const response = await fetch(`${API_BASE_URL}/system/ocr-engines`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get OCR engines');
    }
    
    return response.json();
  },
  
  /**
   * Get system settings
   */
  getSystemSettings: async (): Promise<SystemSettings> => {
    const response = await fetch(`${API_BASE_URL}/system/settings`);
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get system settings');
    }
    
    return response.json();
  },
  
  /**
   * Update system settings
   */
  updateSystemSettings: async (settings: SystemSettings): Promise<SystemSettings> => {
    const response = await fetch(`${API_BASE_URL}/system/settings`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(settings),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update system settings');
    }
    
    return response.json();
  },
};
