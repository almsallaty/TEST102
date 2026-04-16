/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, useRef } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { browser } from "@web/core/browser/browser";

export class ImageEditor extends Component {
    static template = "vehicle_rental.ImageEditor";

    setup() {
        this.canvasRef = useRef("canvas");
        this.recordId = this.props.action.context.record_id;

        this.imageUrl = this.props.action.context.image_url;

        this.rpc = rpc
        this.isDrawing = false;

        onMounted(() => {
            this.initFabric();
        });
    }

    initFabric() {
        const canvasEl = this.canvasRef.el;
        // Set explicit pixel dimensions (required by Fabric.js)
        canvasEl.width = canvasEl.offsetWidth;
        canvasEl.height = canvasEl.offsetHeight;

        this.canvas = new fabric.Canvas(canvasEl, {
            selection: true,
            preserveObjectStacking: true
        });

        // Make drawn paths selectable after creation
        this.canvas.on('path:created', (e) => {
            e.path.set({
                selectable: true,
                hasControls: true,
                hasBorders: true
            });
        });

        // Add color picker change listener
        const colorPicker = document.getElementById('colorPicker');
        if (colorPicker) {
            colorPicker.addEventListener('change', (e) => {
                // If in drawing mode, update brush color immediately
                if (this.canvas.isDrawingMode) {
                    this.canvas.freeDrawingBrush.color = e.target.value;
                }
            });
        }

        if (this.imageUrl) {
            fabric.Image.fromURL(this.imageUrl, (img) => {
                if (!img) {
                    console.error("Failed to load image");
                    return;
                }

                // Set image as not selectable
                img.set({ selectable: false });

                // Add image to canvas
                this.canvas.add(img);

                // Scale image to fit canvas while maintaining aspect ratio
                this.canvas.setWidth(img.width);
                this.canvas.setHeight(img.height);
                this.canvas.setDimensions({
                    width: img.width,
                    height: img.height
                }, { cssOnly: true });

                // Center and zoom to fit
                this.canvas.viewportTransform = [1, 0, 0, 1, 0, 0];
                this.canvas.renderAll();

                // Optional: Add event listener for window resize
                window.addEventListener('resize', () => this.handleResize());

            }, {
                crossOrigin: 'anonymous',
                error: (err) => console.error("Error loading image:", err)
            });
        }
    }

    selectTool(tool) {
        // Always disable free draw first
        this.canvas.isDrawingMode = false;

        switch (tool) {
            case 'draw':
                this.canvas.isDrawingMode = true;
                this.canvas.freeDrawingBrush.color = this.getSelectedColor();
                this.canvas.freeDrawingBrush.width = 3;
                break;
            case 'text':
                this.addText();
                break;
            case 'rectangle':
                this.addRectangle();
                break;
            case 'highlight':
                this.addHighlight();
                break;
            case 'arrow':
                this.addArrow();
                break;
            case 'select':
                // Enable selection mode (drawing mode already disabled above)
                break;
        }
    }

    handleResize() {
        if (!this.canvas || !this.canvasRef || !this.canvasRef.el) {
            return; // Element not available yet
        }

        const canvasEl = this.canvasRef.el;
        canvasEl.width = canvasEl.offsetWidth;
        canvasEl.height = canvasEl.offsetHeight;

        this.canvas.setDimensions({
            width: canvasEl.offsetWidth,
            height: canvasEl.offsetHeight
        });

        this.canvas.renderAll();
    }


    // --- Tools ---
    addText() {
        const text = new fabric.IText('Sample Text', {
            left: 100,
            top: 100,
            fontSize: 20,
            fill: this.getSelectedColor()
        });
        this.canvas.add(text);
    }

    enableFreeDraw() {
        this.canvas.isDrawingMode = true;
        this.canvas.freeDrawingBrush.color = this.getSelectedColor();
        this.canvas.freeDrawingBrush.width = 3;
    }

   addRectangle() {
        const selectedColor = this.getSelectedColor();
        // Convert hex color to rgba with 0.2 opacity
        const fillColor = this.hexToRgba(selectedColor, 0.2);

        const rect = new fabric.Rect({
            left: 100,
            top: 100,
            width: 100,
            height: 60,
            fill: fillColor,
            stroke: selectedColor,
            strokeWidth: 2
        });
        this.canvas.add(rect);
    }

     hexToRgba(hex, alpha) {
        // Remove # if present
        hex = hex.replace('#', '');
        // Parse hex values
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }

    addHighlight() {
        const highlight = new fabric.Rect({
            left: 150,
            top: 150,
            width: 80,
            height: 50,
            fill: "rgba(255,255,0,0.3)",
            selectable: true
        });
        this.canvas.add(highlight);
    }

    getSelectedColor() {
        return document.getElementById('colorPicker').value;
    }

    addArrow(fromX = 200, fromY = 200, toX = 300, toY = 250) {
        const strokeColor = this.getSelectedColor() || 'blue';
        const strokeWidth = 3;

        const dx = toX - fromX;
        const dy = toY - fromY;
        const angle = Math.atan2(dy, dx);
        const length = Math.sqrt(dx*dx + dy*dy);

        const headLength = Math.min(20, length * 0.2);
        const headWidth = headLength * 0.6;

        // Adjust line end to account for arrowhead length
        const adjustedEndX = toX - headLength * Math.cos(angle);
        const adjustedEndY = toY - headLength * Math.sin(angle);

        // Create the line
        const line = new fabric.Line([fromX, fromY, adjustedEndX, adjustedEndY], {
            stroke: strokeColor,
            strokeWidth: strokeWidth,
            strokeLineCap: 'round',
            selectable: false
        });

        const arrowX = toX - (headLength / 2) * Math.cos(angle);
        const arrowY = toY - (headLength / 2) * Math.sin(angle);

        const head = new fabric.Triangle({
            left: arrowX,
            top: arrowY,
            originX: 'center',
            originY: 'center',
            angle: angle * (180 / Math.PI) + 90,
            width: headWidth,
            height: headLength,
            fill: strokeColor,
            selectable: false
        });

        const arrow = new fabric.Group([line, head], {
            selectable: true,
            hasControls: true,
            hasBorders: true,
            lockUniScaling: true,
            lockRotation: false
        });

        this.canvas.add(arrow);
        this.canvas.setActiveObject(arrow);
        this.canvas.requestRenderAll();

        return arrow;
    }

    deleteSelected() {
        const activeObjects = this.canvas.getActiveObjects();
        activeObjects.forEach(obj => this.canvas.remove(obj));
        this.canvas.discardActiveObject();
        this.canvas.requestRenderAll();
    }

    discardChanges() {
        this.env.services.action.doAction({ type: "ir.actions.act_window_close" });
    }

    // --- Save ---
    async saveImage() {
        const dataUrl = this.canvas.toDataURL("image/png");
        await this.rpc("/image_editor/save", {
            record_id: this.recordId,
            model: this.props.action.context.model,
            field_name: this.props.action.context.field_name,
            image_data: dataUrl
        });

        this.env.services.action.doAction({ type: "ir.actions.act_window_close" });
        this.env.bus.trigger("reload");  // 🔄 refresh form in place
    }
}

registry.category("actions").add("image_editor_action", ImageEditor);