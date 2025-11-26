import React, { useRef, useEffect, useState } from 'react';
import * as fabric from 'fabric';
import { Pencil, Eraser, Undo, Save, X } from 'lucide-react';

const ImageEditor = ({ imageUrl, onSave, onCancel }) => {
  const canvasRef = useRef(null);
  const [canvas, setCanvas] = useState(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [editPrompt, setEditPrompt] = useState('');
  const [imageLoaded, setImageLoaded] = useState(false);
  const [loadError, setLoadError] = useState(null); 

  useEffect(() => {
    if (!canvasRef.current) return;

    console.log('=== ImageEditor mounted ===');
    console.log('Received imageUrl:', imageUrl);

    const fabricCanvas = new fabric.Canvas(canvasRef.current, {
      width: 512,
      height: 512,
      isDrawingMode: false,
      backgroundColor: '#f0f0f0'
    });

    // imageUrl 已经是完整路径，直接使用
    const fullUrl = imageUrl.startsWith('http') ? imageUrl : `http://127.0.0.1:8000${imageUrl}`;
    console.log('Loading image from:', fullUrl);

    const img= new Image();
    img.crossOrigin = 'anonymous';

    img.onload = () => {
      console.log('Image loaded successfully:', img.width, 'x', img.height);
      
      const fabricImage=new fabric.Image(img);
      const scale = Math.min(
        fabricCanvas.width / fabricImage.width,
        fabricCanvas.height / fabricImage.height
      );
      
      console.log('Scale factor:', scale);

      fabricImage.set({
        scaleX: scale,
        scaleY: scale,
        left: (fabricCanvas.width - fabricImage.width * scale) / 2,
        top: (fabricCanvas.height - fabricImage.height * scale) / 2,
        selectable: false,
        evented: false
      });

      fabricCanvas.backgroundImage = fabricImage;
      fabricCanvas.renderAll();

      
      setImageLoaded(true);
      setLoadError(null);
      console.log('Background image set successfully');
    }
    img.onerror = (err) => {
      console.error('❌ Failed to load image');
      console.error('Error:', error);
      console.error('URL:', fullUrl);
      setLoadError('Failed to load image from server');
    }
    img.src = fullUrl;
    setCanvas(fabricCanvas);
    // 加载背景图片
    // fabric.Image.fromURL(fullUrl, (img) => {
    //   console.log('Image load callback triggered');
      
    //   if (!img || !img.width || !img.height) {
    //     console.error('Failed to load image or invalid dimensions');
    //     alert('Failed to load image. Please check console for errors.');
    //     return;
    //   }

    //   console.log('Image loaded successfully:', img.width, 'x', img.height);
      
    //   const scale = Math.min(
    //     fabricCanvas.width / img.width,
    //     fabricCanvas.height / img.height
    //   );
      
    //   console.log('Scale factor:', scale);
      
    //   fabricCanvas.setBackgroundImage(img, fabricCanvas.renderAll.bind(fabricCanvas), {
    //     scaleX: scale,
    //     scaleY: scale,
    //     left: (fabricCanvas.width - img.width * scale) / 2,
    //     top: (fabricCanvas.height - img.height * scale) / 2
    //   });
      
    //   setImageLoaded(true);
    //   console.log('Background image set successfully');
    // }, {
    //   crossOrigin: 'anonymous'
    // });

    // setCanvas(fabricCanvas);

    return () => {
      console.log('Disposing canvas');
      fabricCanvas.dispose();
    };
  }, [imageUrl]);

  const enableDrawing = () => {
    if (!canvas) {
      console.log('Canvas not ready');
      return;
    }
    
    console.log('Enabling drawing mode...');
    canvas.isDrawingMode = true;
    
    // 检查并初始化画笔
    if (!canvas.freeDrawingBrush) {
      console.log('Creating new PencilBrush');
      canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
    }
    
    canvas.freeDrawingBrush.color = 'red';
    canvas.freeDrawingBrush.width = 5;
    
    setIsDrawing(true);
    console.log('✏️ Drawing enabled');
  };

  const disableDrawing = () => {
    if (canvas) {
      canvas.isDrawingMode = false;
      setIsDrawing(false);
      console.log('Drawing disabled');
    }
  };

  const handleUndo = () => {
    if (canvas) {
      const objects = canvas.getObjects();
      if (objects.length > 0) {
        canvas.remove(objects[objects.length - 1]);
        canvas.renderAll();
        console.log('Undo performed');
      }
    }
  };

  const handleSave = async () => {
    if (!canvas) return;

    console.log('Saving canvas...');
    canvas.isDrawingMode = false;
    const dataURL = canvas.toDataURL({
      format: 'png',
      quality: 1
    });
    const blob = await (await fetch(dataURL)).blob();
    
    console.log('Canvas saved, blob size:', blob.size);
    console.log('Edit prompt:', editPrompt);
    
    // 传递 blob 和 prompt
    onSave(blob, editPrompt);
  };

  return (
    <div className="flex flex-col items-center gap-4 p-6 bg-white rounded-lg">
      <div className="w-full flex items-center justify-between mb-2">
        <h3 className="text-lg font-semibold">Draw on Image & Describe Changes</h3>
        <button onClick={onCancel} className="text-gray-400 hover:text-gray-600">
          <X className="w-5 h-5" />
        </button>
      </div>
      
      {/* 画布 */}
      <div className="border-2 border-gray-300 rounded-lg shadow-md relative">
        {!imageLoaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100 z-10">
            <div className="text-center">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto mb-2"></div>
              <p className="text-sm text-gray-500">Loading image...</p>
            </div>
          </div>
        )}
        <canvas ref={canvasRef} />
      </div>
      
      {/* Prompt 输入框 */}
      <div className="w-full">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Describe your changes (optional but recommended):
        </label>
        <textarea
          value={editPrompt}
          onChange={(e) => setEditPrompt(e.target.value)}
          placeholder="e.g., 'Remove the marked areas', 'Smooth the edges I circled', 'Fill in the hole marked in red'..."
          className="w-full border rounded-lg px-4 py-3 focus:ring-2 focus:ring-purple-500 focus:outline-none resize-none"
          rows={3}
        />
      </div>

      {/* 工具栏 */}
      <div className="flex gap-2 flex-wrap justify-center w-full">
        <button
          onClick={enableDrawing}
          disabled={!imageLoaded}
          className={`px-4 py-2 rounded-lg flex items-center gap-2 transition-colors ${
            isDrawing ? 'bg-red-600 text-white' : 'bg-gray-200 hover:bg-gray-300'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          <Pencil className="w-4 h-4" />
          Draw
        </button>
        
        <button
          onClick={disableDrawing}
          disabled={!imageLoaded}
          className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50"
        >
          <Eraser className="w-4 h-4" />
          Select
        </button>
        
        <button
          onClick={handleUndo}
          disabled={!imageLoaded}
          className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg flex items-center gap-2 transition-colors disabled:opacity-50"
        >
          <Undo className="w-4 h-4" />
          Undo
        </button>
        
        <button
          onClick={handleSave}
          disabled={!imageLoaded}
          className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="w-4 h-4" />
          Save & Apply
        </button>
        
        <button
          onClick={onCancel}
          className="px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors"
        >
          Cancel
        </button>
      </div>

      {/* 使用提示 */}
      <div className="w-full bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm text-blue-800">
        <p className="font-medium mb-1">💡 How to use:</p>
        <ol className="list-decimal list-inside space-y-1 text-xs">
          <li>Wait for the image to load (gray background will disappear)</li>
          <li>Click "Draw" and mark areas you want to change with red lines</li>
          <li>Describe what changes you want in the text box above</li>
          <li>Click "Save & Apply" to generate the edited version</li>
        </ol>
      </div>
    </div>
  );
};

export default ImageEditor;