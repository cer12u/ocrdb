import { useState, useEffect } from 'react'
import './App.css'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs'
import { UploadForm } from './components/UploadForm'
import { DocumentList } from './components/DocumentList'
import { SearchBar } from './components/SearchBar'
import { systemApi, StorageInfo } from './lib/api'
import { Toaster } from './components/ui/toaster'
import { Database, Upload, Search, FolderTree, Settings } from 'lucide-react'

function App() {
  const [activeTab, setActiveTab] = useState('documents')
  const [searchQuery, setSearchQuery] = useState('')
  // const [currentFolder, setCurrentFolder] = useState('/')
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const [storageInfo, setStorageInfo] = useState<StorageInfo | null>(null)

  useEffect(() => {
    const loadStorageInfo = async () => {
      try {
        const info = await systemApi.getStorageInfo()
        setStorageInfo(info)
      } catch (error) {
        console.error('Failed to load storage info:', error)
      }
    }

    loadStorageInfo()
    const interval = setInterval(loadStorageInfo, 30000)
    return () => clearInterval(interval)
  }, [refreshTrigger])

  const handleUploadComplete = () => {
    setRefreshTrigger(prev => prev + 1)
  }

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setActiveTab('search')
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto py-4 px-4 flex justify-between items-center">
          <div className="flex items-center">
            <Database className="h-6 w-6 mr-2" />
            <h1 className="text-xl font-bold">OCR Database</h1>
          </div>
          <div className="flex-1 max-w-lg mx-4">
            <SearchBar onSearch={handleSearch} />
          </div>
          <div className="text-sm text-muted-foreground">
            {storageInfo && (
              <span>
                {storageInfo.total_documents} documents • {formatBytes(storageInfo.total_size)}
              </span>
            )}
          </div>
        </div>
      </header>

      <main className="container mx-auto py-6 px-4">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="mb-6">
            <TabsTrigger value="documents">
              <Database className="h-4 w-4 mr-2" />
              Documents
            </TabsTrigger>
            <TabsTrigger value="upload">
              <Upload className="h-4 w-4 mr-2" />
              Upload
            </TabsTrigger>
            <TabsTrigger value="search" disabled={!searchQuery}>
              <Search className="h-4 w-4 mr-2" />
              Search Results
            </TabsTrigger>
            <TabsTrigger value="folders">
              <FolderTree className="h-4 w-4 mr-2" />
              Folders
            </TabsTrigger>
            <TabsTrigger value="settings">
              <Settings className="h-4 w-4 mr-2" />
              Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="documents" className="space-y-6">
            <h2 className="text-2xl font-bold">All Documents</h2>
            <DocumentList refreshTrigger={refreshTrigger} />
          </TabsContent>

          <TabsContent value="upload" className="space-y-6">
            <h2 className="text-2xl font-bold">Upload Document</h2>
            <div className="flex justify-center">
              <UploadForm onUploadComplete={handleUploadComplete} />
            </div>
          </TabsContent>

          <TabsContent value="search" className="space-y-6">
            <h2 className="text-2xl font-bold">Search Results: "{searchQuery}"</h2>
            <DocumentList searchQuery={searchQuery} refreshTrigger={refreshTrigger} />
          </TabsContent>

          <TabsContent value="folders" className="space-y-6">
            <h2 className="text-2xl font-bold">Folders</h2>
            <p className="text-muted-foreground">
              Folder view will be implemented in a future update.
            </p>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            <h2 className="text-2xl font-bold">Settings</h2>
            <p className="text-muted-foreground">
              Settings will be implemented in a future update.
            </p>
          </TabsContent>
        </Tabs>
      </main>

      <Toaster />
    </div>
  )
}

export default App
