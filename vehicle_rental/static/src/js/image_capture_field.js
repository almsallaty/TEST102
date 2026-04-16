/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";
import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

/**
 * Camera Capture Dialog Component
 */
class CameraCaptureDialog extends Component {
    static template = "vehicle_rental.CameraCaptureDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        onCapture: Function,
    };

    setup() {
        this.state = useState({
            cameraReady: false,
            error: null,
            previewImage: null,
            facingMode: "environment",
            stream: null,
        });

        this.videoRef = useRef("videoElement");
        this.canvasRef = useRef("canvasElement");

        onMounted(() => this.startCamera());
        onWillUnmount(() => this.stopCamera());
    }

    async startCamera() {
        try {
            this.state.error = null;
            this.state.cameraReady = false;
            this.stopCamera();

            const constraints = {
                video: {
                    facingMode: this.state.facingMode,
                    width: { ideal: 1920 },
                    height: { ideal: 1080 },
                },
                audio: false,
            };

            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            this.state.stream = stream;

            if (this.videoRef.el) {
                this.videoRef.el.srcObject = stream;
                await this.videoRef.el.play();
                this.state.cameraReady = true;
            }
        } catch (error) {
            console.error("Camera access error:", error);
            this.state.error = this.getErrorMessage(error);
        }
    }

    getErrorMessage(error) {
        if (error.name === "NotAllowedError") {
            return _t("Camera access denied. Please allow camera access in your browser settings.");
        } else if (error.name === "NotFoundError") {
            return _t("No camera found. Please connect a camera and try again.");
        } else if (error.name === "NotReadableError") {
            return _t("Camera is in use by another application.");
        }
        return _t("Unable to access camera: ") + error.message;
    }

    stopCamera() {
        if (this.state.stream) {
            this.state.stream.getTracks().forEach(track => track.stop());
            this.state.stream = null;
        }
        if (this.videoRef.el) {
            this.videoRef.el.srcObject = null;
        }
    }

    async switchCamera() {
        this.state.facingMode = this.state.facingMode === "environment" ? "user" : "environment";
        await this.startCamera();
    }

    capturePhoto() {
        if (!this.videoRef.el || !this.canvasRef.el) return;

        const video = this.videoRef.el;
        const canvas = this.canvasRef.el;
        const context = canvas.getContext("2d");

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        const imageData = canvas.toDataURL("image/jpeg", 0.9);
        this.state.previewImage = imageData;
        video.pause();
    }

    retakePhoto() {
        this.state.previewImage = null;
        if (this.videoRef.el) {
            this.videoRef.el.play();
        }
    }

    confirmCapture() {
        if (this.state.previewImage) {
            const base64Data = this.state.previewImage.split(",")[1];
            const filename = `capture_${Date.now()}.jpg`;
            const fileSize = Math.round((base64Data.length * 3) / 4);

            this.props.onCapture({
                data: base64Data,
                filename: filename,
                captureMethod: "camera",
                fileSize: fileSize,
            });

            this.stopCamera();
            this.props.close();
        }
    }

    onClose() {
        this.stopCamera();
        this.props.close();
    }
}

/**
 * Image Capture One2Many Field Widget
 */
export class ImageCaptureOne2ManyField extends X2ManyField {
    static template = "vehicle_rental.ImageCaptureOne2ManyField";

    static props = {
        ...X2ManyField.props,
    };

    setup() {
        super.setup();

        this.state = useState({
            isProcessing: false,
            isDragging: false,
            lightboxImage: null,
        });

        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.fileInputRef = useRef("fileInput");
    }

    get isCameraAvailable() {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    }

    get previewImages() {
        if (!this.list || !this.list.records) return [];

        return this.list.records.map((record, index) => {
            let imageData = record.data.avatar;
            let resId = record.resId;

            // Get file size from stored field
            let sizeInBytes = record.data.file_size || 0;

            // Fallback: calculate from base64 if no stored size and we have actual base64 data
            if (!sizeInBytes && imageData && typeof imageData === 'string') {
                if (imageData.length > 1000) {
                    const base64Data = imageData.includes(',') ? imageData.split(',')[1] : imageData;
                    sizeInBytes = Math.round((base64Data.length * 3) / 4);
                }
            }

            return {
                id: record.id || `temp_${index}`,
                resId: resId,
                data: imageData,
                name: record.data.name || 'Image',
                filename: record.data.image_filename,
                captureMethod: record.data.capture_method,
                captureDate: record.data.capture_date,
                index: index,
                isSaved: !!resId,
                sizeInBytes: sizeInBytes,
                sizeFormatted: this.formatFileSize(sizeInBytes),
                sizeCategory: this.getSizeCategory(sizeInBytes),
            };
        }).filter(img => img.data || img.isSaved);
    }

    formatFileSize(bytes) {
        if (!bytes || bytes === 0) return '';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    }

    getSizeCategory(bytes) {
        const KB = 1024;
        const MB = 1024 * KB;

        if (bytes < 500 * KB) {
            return 'small';
        } else if (bytes < 2 * MB) {
            return 'medium';
        } else {
            return 'large';
        }
    }

    getImageSrc(img) {
        if (img && img.resId) {
            const resModel = this.list.resModel;
            return `/web/image/${resModel}/${img.resId}/avatar`;
        }

        if (img && img.data) {
            if (typeof img.data === 'string' && img.data.startsWith('data:')) {
                return img.data;
            }
            return `data:image/jpeg;base64,${img.data}`;
        }

        return '';
    }

    getImageSrcFromData(imageData) {
        if (!imageData) return '';
        if (typeof imageData === 'string' && imageData.startsWith('data:')) {
            return imageData;
        }
        return `data:image/jpeg;base64,${imageData}`;
    }

    getRecordImageSrc(record) {
        if (record.resId) {
            const resModel = this.list.resModel;
            return `/web/image/${resModel}/${record.resId}/avatar`;
        }

        if (record.data && record.data.avatar) {
            const imageData = record.data.avatar;
            if (typeof imageData === 'string' && imageData.startsWith('data:')) {
                return imageData;
            }
            return `data:image/jpeg;base64,${imageData}`;
        }

        return '';
    }

    openCameraDialog() {
        if (this.props.readonly) return;

        this.dialog.add(CameraCaptureDialog, {
            onCapture: (imageData) => this.addImage(imageData),
        });
    }

    triggerFileUpload() {
        if (this.props.readonly) return;
        if (this.fileInputRef.el) {
            this.fileInputRef.el.click();
        }
    }

    async onFileSelect(event) {
        const files = event.target.files;
        if (files.length > 0) {
            await this.processFiles(files);
        }
        event.target.value = "";
    }

    onDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        this.state.isDragging = true;
    }

    onDragLeave(event) {
        event.preventDefault();
        event.stopPropagation();
        this.state.isDragging = false;
    }

    async onDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        this.state.isDragging = false;

        if (this.props.readonly) return;

        const files = event.dataTransfer.files;
        if (files.length > 0) {
            await this.processFiles(files);
        }
    }

    async processFiles(files) {
        for (const file of files) {
            if (!file.type.startsWith("image/")) {
                this.notification.add(_t("File '%s' is not an image", file.name), { type: "warning" });
                continue;
            }

            if (file.size > 10 * 1024 * 1024) {
                this.notification.add(_t("File '%s' is too large (max 10MB)", file.name), { type: "warning" });
                continue;
            }

            const base64Data = await this.fileToBase64(file);
            await this.addImage({
                data: base64Data,
                filename: file.name,
                captureMethod: "upload",
                fileSize: file.size,
            });
        }
    }

    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => {
                const base64 = reader.result.split(",")[1];
                resolve(base64);
            };
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    async addImage(imageData) {
        if (this.state.isProcessing) return;

        this.state.isProcessing = true;

        try {
            // Calculate file size
            let fileSize = imageData.fileSize || 0;
            if (!fileSize && imageData.data) {
                const base64Str = imageData.data.includes(',')
                    ? imageData.data.split(',')[1]
                    : imageData.data;
                fileSize = Math.round((base64Str.length * 3) / 4);
            }

            // Ensure list is properly initialized
            if (!this.list) {
                console.error('List is not initialized');
                throw new Error('List is not initialized');
            }

            // Prepare the data to be added
            const updateData = {
                avatar: imageData.data,
                image_filename: imageData.filename,
                capture_method: imageData.captureMethod || 'upload',  // Default to 'upload' if not provided
                file_size: fileSize,
                sequence: this.list.records.length * 10,
            };

            // Add title/name field if it exists
            if (imageData.filename) {
                updateData.name = imageData.filename;
            }

            let record;

            try {
                // Method 1: Try using the command pattern directly (most reliable)
                const commands = [[0, 0, updateData]];
                await this.props.record.update({
                    [this.props.name]: commands,
                });

                this.notification.add(_t("Image added successfully"), { type: "success" });
            } catch (e) {
                console.error('Error with command pattern, trying alternative:', e);

                // Method 2: Fallback - try with context
                try {
                    const context = this.list.context || {};
                    record = await this.list.addNewRecord({
                        position: 'bottom',
                        context: context,
                    });

                    if (record) {
                        await record.update(updateData);
                        this.notification.add(_t("Image added successfully"), { type: "success" });
                    }
                } catch (e2) {
                    console.error('Error with context method:', e2);

                    // Method 3: Last resort - direct edit
                    const currentValue = this.props.record.data[this.props.name] || [];
                    const newValue = [...currentValue, [0, 0, updateData]];

                    await this.props.record.update({
                        [this.props.name]: newValue,
                    });

                    this.notification.add(_t("Image added successfully"), { type: "success" });
                }
            }

        } catch (error) {
            console.error("Error adding image:", error);
            this.notification.add(_t("Failed to add image: ") + error.message, { type: "danger" });
        } finally {
            this.state.isProcessing = false;
        }
    }

    async removeImage(index) {
        if (this.props.readonly) return;

        try {
            const records = this.list.records;

            if (index >= 0 && index < records.length) {
                const record = records[index];
                await this.deleteRecord(record);

                this.notification.add(_t("Image removed"), { type: "info" });
            }
        } catch (error) {
            console.error("Error removing image:", error);
            this.notification.add(_t("Failed to remove image"), { type: "danger" });
        }
    }

    async removeImageByRecord(record) {
        if (this.props.readonly) return;

        try {
            await this.deleteRecord(record);

            this.notification.add(_t("Image removed"), { type: "info" });
        } catch (error) {
            console.error("Error removing image:", error);
            this.notification.add(_t("Failed to remove image"), { type: "danger" });
        }
    }

    async deleteRecord(record) {
        // FIX 8: More robust deletion handling
        try {
            // Method 1: Try using list.delete (Odoo 17+)
            if (this.list && typeof this.list.delete === 'function') {
                await this.list.delete(record);
                return;
            }

            // Method 2: Try using list.removeRecord
            if (this.list && typeof this.list.removeRecord === 'function') {
                await this.list.removeRecord(record);
                return;
            }

            // Method 3: Use Odoo commands
            const resId = record.resId;
            if (resId) {
                // For saved records: command 2 = delete and unlink
                await this.props.record.update({
                    [this.props.name]: [[2, resId, false]],
                });
            } else {
                // For new/virtual records: command 3 = unlink (cut link)
                await this.props.record.update({
                    [this.props.name]: [[3, record.id, false]],
                });
            }
        } catch (error) {
            console.error('Error in deleteRecord:', error);
            throw error;
        }
    }

    openLightbox(img) {
        this.state.lightboxImage = img;
        document.body.style.overflow = 'hidden';
    }

    closeLightbox() {
        this.state.lightboxImage = null;
        document.body.style.overflow = '';
    }

    navigateLightbox(direction) {
        if (!this.state.lightboxImage) return;

        const currentIndex = this.state.lightboxImage.index;
        const newIndex = currentIndex + direction;

        if (newIndex >= 0 && newIndex < this.previewImages.length) {
            this.state.lightboxImage = this.previewImages[newIndex];
        }
    }

    async downloadImage(img, event) {
        if (event) {
            event.stopPropagation();
        }

        try {
            const imageSrc = this.getImageSrc(img);
            const filename = img.filename || img.name || `image_${Date.now()}.jpg`;

            if (imageSrc.startsWith('/web/image')) {
                const response = await fetch(imageSrc);
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                this.triggerDownload(url, filename);
                window.URL.revokeObjectURL(url);
            } else {
                this.triggerDownload(imageSrc, filename);
            }

            this.notification.add(_t("Image downloaded"), { type: "success" });
        } catch (error) {
            console.error("Error downloading image:", error);
            this.notification.add(_t("Failed to download image"), { type: "danger" });
        }
    }

    triggerDownload(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    async confirmDelete(img, event) {
        if (event) {
            event.stopPropagation();
        }

        if (this.props.readonly) return;

        if (confirm(_t("Are you sure you want to delete this image?"))) {
            await this.removeImage(img.index);
            if (this.state.lightboxImage && this.state.lightboxImage.id === img.id) {
                this.closeLightbox();
            }
        }
    }

    async downloadImageFromRecord(record) {
        try {
            const imageSrc = this.getRecordImageSrc(record);
            const filename = record.data.image_filename || record.data.name || `image_${Date.now()}.jpg`;

            if (imageSrc.startsWith('/web/image')) {
                const response = await fetch(imageSrc);
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                this.triggerDownload(url, filename);
                window.URL.revokeObjectURL(url);
            } else {
                this.triggerDownload(imageSrc, filename);
            }

            this.notification.add(_t("Image downloaded"), { type: "success" });
        } catch (error) {
            console.error("Error downloading image:", error);
            this.notification.add(_t("Failed to download image"), { type: "danger" });
        }
    }

    async confirmDeleteRecord(record) {
        if (this.props.readonly) return;

        if (confirm(_t("Are you sure you want to delete this image?"))) {
            await this.removeImageByRecord(record);
        }
    }
}

// Field definition
export const imageCaptureOne2ManyField = {
    ...x2ManyField,
    component: ImageCaptureOne2ManyField,
    displayName: _t("Image Capture One2Many"),
    supportedTypes: ["one2many"],
};

// Register the widget
registry.category("fields").add("image_capture_one2many", imageCaptureOne2ManyField);