// File Upload Handler with Multi-file Support
document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('fileInput');
    const fileDropArea = document.getElementById('fileDropArea');
    const filePreview = document.getElementById('filePreview');
    const filePreviewContainer = document.getElementById('filePreviewContainer');
    const fileCount = document.getElementById('fileCount');
    const uploadForm = document.getElementById('uploadForm');
    const uploadBtn = document.getElementById('uploadBtn');
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    let selectedFiles = [];
    
    if (fileInput && fileDropArea) {
        // File selection handler
        fileInput.addEventListener('change', function(e) {
            handleFileSelect(e.target.files);
        });
        
        // Drag and drop handlers
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileDropArea.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            fileDropArea.addEventListener(eventName, highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            fileDropArea.addEventListener(eventName, unhighlight, false);
        });
        
        fileDropArea.addEventListener('drop', handleDrop, false);
    }
    
    // Form submission with progress
    if (uploadForm) {
        uploadForm.addEventListener('submit', function(e) {
            if (!fileInput.files || fileInput.files.length === 0) {
                return;
            }
            
            // Check if any file is large
            let totalSize = 0;
            for (let i = 0; i < fileInput.files.length; i++) {
                totalSize += fileInput.files[i].size;
            }
            
            // For large uploads, show progress indicator
            if (totalSize > 10 * 1024 * 1024) { // If total > 10MB
                e.preventDefault();
                uploadWithProgress();
            }
        });
    }
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight() {
        fileDropArea.classList.add('highlight');
    }
    
    function unhighlight() {
        fileDropArea.classList.remove('highlight');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFileSelect(files);
    }
    
    function handleFileSelect(files) {
        if (files && files.length > 0) {
            selectedFiles = Array.from(files);
            displayFilePreviews();
        }
    }
    
    function displayFilePreviews() {
        if (selectedFiles.length === 0) {
            filePreview.style.display = 'none';
            fileDropArea.style.display = 'block';
            return;
        }
        
        // Update file count
        const countText = selectedFiles.length === 1 ? '1 file selected' : `${selectedFiles.length} files selected`;
        fileCount.textContent = countText;
        
        // Clear existing previews
        filePreviewContainer.innerHTML = '';
        
        // Create preview for each file
        selectedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-preview-item';
            fileItem.innerHTML = `
                <div class="file-preview-content">
                    <i class="fas fa-file file-preview-icon"></i>
                    <div class="file-preview-info">
                        <p class="file-preview-name">${escapeHtml(file.name)}</p>
                        <p class="file-preview-size">${formatFileSize(file.size)}</p>
                    </div>
                    <button type="button" class="file-remove-btn-small" onclick="removeFileAtIndex(${index})" title="Remove">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            filePreviewContainer.appendChild(fileItem);
        });
        
        // Show preview section, hide drop area
        filePreview.style.display = 'block';
        fileDropArea.style.display = 'none';
        
        // Update the file input with current files
        updateFileInput();
    }
    
    function updateFileInput() {
        // Create a new DataTransfer object
        const dataTransfer = new DataTransfer();
        selectedFiles.forEach(file => {
            dataTransfer.items.add(file);
        });
        fileInput.files = dataTransfer.files;
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Make removeFileAtIndex available globally
    window.removeFileAtIndex = function(index) {
        selectedFiles.splice(index, 1);
        displayFilePreviews();
    };
    
    function uploadWithProgress() {
        const formData = new FormData(uploadForm);
        
        uploadBtn.disabled = true;
        progressContainer.style.display = 'block';
        
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percentComplete = Math.round((e.loaded / e.total) * 100);
                progressFill.style.width = percentComplete + '%';
                const fileText = selectedFiles.length === 1 ? '1 file' : `${selectedFiles.length} files`;
                progressText.textContent = `Uploading ${fileText}... ${percentComplete}%`;
            }
        });
        
        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                progressText.textContent = 'Upload complete! Redirecting...';
                progressFill.style.width = '100%';
                setTimeout(function() {
                    window.location.href = '/';
                }, 1000);
            } else {
                progressText.textContent = 'Upload failed!';
                progressFill.style.background = 'var(--danger-color)';
                uploadBtn.disabled = false;
            }
        });
        
        xhr.addEventListener('error', function() {
            progressText.textContent = 'Upload failed!';
            progressFill.style.background = 'var(--danger-color)';
            uploadBtn.disabled = false;
        });
        
        xhr.open('POST', uploadForm.action);
        xhr.send(formData);
    }
});

// Remove all files function
function removeAllFiles() {
    const fileInput = document.getElementById('fileInput');
    const filePreview = document.getElementById('filePreview');
    const fileDropArea = document.getElementById('fileDropArea');
    
    fileInput.value = '';
    filePreview.style.display = 'none';
    fileDropArea.style.display = 'block';
    
    // Reset selectedFiles array if it exists
    if (typeof selectedFiles !== 'undefined') {
        selectedFiles = [];
    }
}

// Auto-hide flash messages after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });
});

// Detect device type and log to console (for debugging)
document.addEventListener('DOMContentLoaded', function() {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isTablet = /(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(navigator.userAgent);
    
    console.log('Device Detection:');
    console.log('Mobile:', isMobile);
    console.log('Tablet:', isTablet);
    console.log('Desktop:', !isMobile && !isTablet);
    console.log('User Agent:', navigator.userAgent);
    
    // Add device class to body for potential CSS targeting
    if (isMobile) {
        document.body.classList.add('mobile-device');
    } else if (isTablet) {
        document.body.classList.add('tablet-device');
    } else {
        document.body.classList.add('desktop-device');
    }
});

