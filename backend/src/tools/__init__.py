from .base_tools import BaseTool, FrontmatterManagerTool

# Flow-based tools (organized by Flow number from flows.md)
from .note_tools import NotesTool  # Flow 2: Semantic Notes Access and Editing Flow
try:
    from .reorganization_tools import VaultReorganizationTool  # Flow 4: Vault Reorganization Flow
except ImportError:
    pass  # In case the class doesn't exist yet
try:
    from .service_execution_tool import ServiceExecutionTool  # Flow 5: Service Execution Flow
except ImportError:
    pass  # In case the file doesn't exist yet
try:
    from .template_tools import TemplateTool  # Flow 6: Template Management Flow
except ImportError:
    pass  # In case the class doesn't exist yet
try:
    from .tag_tools import TagTool  # Flow 7: Tag Management Flow
except ImportError:
    pass  # In case the class doesn't exist yet
try:
    from .text_tools import ContentTool  # Flow 8: Content Processing Flow
except ImportError:
    pass  # In case the class doesn't exist yet

# Legacy tools - these will be replaced by the flow-based tools
from .note_tools import (
    CreateNoteTool,
    UpdateNoteTool,
    DeleteNoteTool,
    ListNotesTool,
    SearchNotesTool
)
from .folder_tools import (
    CreateFolderTool,
    DeleteFolderTool,
    MoveFolderTool,
    ListFoldersTool,
    GetFolderContentsTool
)
from .tag_tools import TagManagerTool
from .template_tools import (
    CreateTemplateTool,
    DeleteTemplateTool,
    ListTemplatesTool,
    ApplyTemplateTool,
    GetTemplateContentTool
)
from .audio_tools import (
    TranscribeAudioTool,
    ListAudioFilesTool,
    GetTranscriptionNoteTool
)
from .email_tools import (
    ProcessEmailTool,
    ListEmailFilesTool,
    GetEmailNoteTool
)
from .indexing_tools import (
    IndexNoteTool,
    SearchNotesTool,
    ClusterNotesTool
)
from .semantic_tools import (
    AnalyzeRelationshipsTool,
    FindRelatedNotesTool,
    GenerateKnowledgeGraphTool
)
from .reorganization_tools import (
    AnalyzeVaultStructureTool,
    ReorganizeVaultTool,
    SuggestOrganizationTool
)
from .hierarchy_tools import HierarchyManagerTool

__all__ = [
    # Base
    'BaseTool',
    'FrontmatterManagerTool',
    
    # Flow-based tools (primary tools that implement flows.md)
    'NotesTool',                # Flow 2: Semantic Notes Access and Editing Flow
    'VaultReorganizationTool',  # Flow 4: Vault Reorganization Flow
    'ServiceExecutionTool',     # Flow 5: Service Execution Flow
    'TemplateTool',             # Flow 6: Template Management Flow
    'TagTool',                  # Flow 7: Tag Management Flow 
    'ContentTool',              # Flow 8: Content Processing Flow
    
    # Legacy tools - these will be gradually replaced by the flow-based tools
    
    # Note Management
    'CreateNoteTool',
    'UpdateNoteTool',
    'DeleteNoteTool',
    'ListNotesTool',
    'SearchNotesTool',
    
    # Folder Management
    'CreateFolderTool',
    'DeleteFolderTool',
    'MoveFolderTool',
    'ListFoldersTool',
    'GetFolderContentsTool',
    
    # Tag Management
    'TagManagerTool',
    
    # Template Management
    'CreateTemplateTool',
    'DeleteTemplateTool',
    'ListTemplatesTool',
    'ApplyTemplateTool',
    'GetTemplateContentTool',
    
    # Audio Processing
    'TranscribeAudioTool',
    'ListAudioFilesTool',
    'GetTranscriptionNoteTool',
    
    # Email Processing
    'ProcessEmailTool',
    'ListEmailFilesTool',
    'GetEmailNoteTool',
    
    # Indexing and Search
    'IndexNoteTool',
    'SearchNotesTool',
    'ClusterNotesTool',
    
    # Semantic Analysis
    'AnalyzeRelationshipsTool',
    'FindRelatedNotesTool',
    'GenerateKnowledgeGraphTool',
    
    # Vault Reorganization
    'AnalyzeVaultStructureTool',
    'ReorganizeVaultTool',
    'SuggestOrganizationTool',

    # Hierarchy Management
    'HierarchyManagerTool'
] 