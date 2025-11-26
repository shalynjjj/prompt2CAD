import React, { useState } from 'react';
import axios from 'axios';
import ImageEditor from './components/ImageEditor';
import { Upload, Edit3, Box, ArrowRight, RefreshCw, Download, AlertCircle } from 'lucide-react';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

function App() {
  // --- 状态管理 ---
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showEditor, setShowEditor] = useState(false);
  
  const [sessionId, setSessionId] = useState('');
  const [images, setImages] = useState({ original: null, current2d: null });
  const [editPrompt, setEditPrompt] = useState('');
  const [editVersion, setEditVersion] = useState(2);
  const [result3D, setResult3D] = useState({ stlUrl: null, previewUrl: null });

  // --- 辅助函数 ---
  const urlToBlob = async (url) => {
    const response = await fetch(url);
    const blob = await response.blob();
    return new File([blob], "current_sketch.png", { type: "image/png" });
  };

  // --- Step 1: 生成 2D ---
  const handleGenerate2D = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await axios.post(`${API_BASE_URL}/generate2d`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (res.data.success) {
        setSessionId(res.data.session_id);
        const silhouette2d = res.data.data.silhouette_2d;
        setImages({
          original: URL.createObjectURL(file),
          current2d: silhouette2d.url_path
        });
        setStep(2);
      } else {
        setError(res.data.error || 'generate2D failed');
      }
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Request error');
    } finally {
      setLoading(false);
    }
  };

  // --- Step 2: Edit 2D (文字描述) ---
  const handleEdit2D = async () => {
    if (!editPrompt) return;
    setLoading(true);
    setError(null);

    try {
      const imageFile = await urlToBlob(images.current2d);

      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('prompt', editPrompt);
      formData.append('image', imageFile);
      formData.append('version', editVersion);

      const res = await axios.post(`${API_BASE_URL}/edit2d`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      if (res.data.success) {
        setImages(prev => ({ ...prev, current2d: res.data.data.silhouette_url }));
        setEditVersion(prev => prev + 1);
        setEditPrompt('');
      } else {
        setError(res.data.error || '编辑失败');
      }
    } catch (err) {
      setError(err.response?.data?.detail || '编辑请求失败');
    } finally {
      setLoading(false);
    }
  };

  // --- Step 2: Edit 2D (画布编辑) ---
  const handleEditorSave = async (blob, prompt) => {  // 接收两个参数
  setLoading(true);
  setError(null);

  try {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('image', blob, 'edited.png');
    formData.append('prompt', prompt || 'Apply the changes marked in red');  // 使用传入的 prompt
    formData.append('version', editVersion);

    const res = await axios.post(`${API_BASE_URL}/edit2d`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });

    if (res.data.success) {
      setImages(prev => ({ 
        ...prev, 
        current2d: res.data.data.silhouette_2d.url_path 
      }));
      setEditVersion(prev => prev + 1);
      setShowEditor(false);
      setEditPrompt('');
    } else {
      setError(res.data.error || '编辑失败');
    }
  } catch (err) {
    console.error('Edit error:', err);
    setError(err.response?.data?.detail || '编辑请求失败');
  } finally {
    setLoading(false);
  }
};
  // --- Step 3: 生成 3D ---
  const handleGenerate3D = async () => {
    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append('session_id', sessionId);
    if (editPrompt) {
      formData.append('prompt', editPrompt); 
    }

    try {
      const res = await axios.post(`${API_BASE_URL}/generate3D`, formData);
      console.log('3D generation response:', res.data);
      console.log('res.data.success:', res.data.success); 
      console.log('res.data.data:', res.data.data);
      console.log('res.data.stl')
      if (res.data.success) {
        const { stl_file, render_image } = res.data.data;
        console.log("before extracting files");
        const stlUrl = stl_file?.url_path 
          ? `http://127.0.0.1:8000${stl_file.url_path}`
          : null;
        console.log("after extracting stlUrl");
        const previewUrl = render_image?.url_path 
          ? `http://127.0.0.1:8000${render_image.url_path}`
          : null;
        console.log('STL URL:', stlUrl);
        console.log('Preview URL:', previewUrl);
        setResult3D({
          stlUrl: stlUrl,
          previewUrl: previewUrl
        });
        console.log('3D generation successful:', stlUrl, previewUrl);
        setStep(3);
      } else {
        setError(res.data.error || '3d generation failed');
      }
    } catch (err) {
      setError(err.response?.data?.detail || '3D generation request failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadSTL=async()=>{
    if(!result3D.stlUrl){
      console.error("No STL URL available for download.");
      return;
    }
    console.log('Downloading STL from:', result3D.stlUrl);
    const link = document.createElement('a');
    link.href = result3D.stlUrl;
    link.download = `keychain_${sessionId}.stl`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // --- UI 渲染 ---
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center py-10 px-4">
      <h1 className="text-3xl font-bold text-gray-800 mb-2">3D KeyChain Maker</h1>
      <p className="text-gray-500 mb-8">From Sketch to STL in seconds</p>

      {/* 进度条 */}
      <div className="w-full max-w-3xl flex justify-between mb-8 px-10">
        {[1, 2, 3].map((s) => (
          <div key={s} className={`flex flex-col items-center ${step >= s ? 'text-blue-600' : 'text-gray-300'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold mb-2 ${step >= s ? 'bg-blue-100' : 'bg-gray-200'}`}>
              {s}
            </div>
            <span className="text-xs font-medium">
              {s === 1 ? 'Upload' : s === 2 ? 'Edit 2D' : 'Download 3D'}
            </span>
          </div>
        ))}
      </div>

      {/* 主卡片 */}
      <div className="bg-white rounded-xl shadow-lg w-full max-w-3xl p-8 relative min-h-[400px]">
        
        {/* Loading Overlay */}
        {loading && (
          <div className="absolute inset-0 bg-white/80 z-50 flex flex-col items-center justify-center rounded-xl">
            <RefreshCw className="w-10 h-10 text-blue-600 animate-spin mb-4" />
            <p className="text-blue-600 font-medium">Processing... usually takes 10-30s</p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6 flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            {error}
          </div>
        )}

        {/* --- STEP 1: 上传 --- */}
        {step === 1 && (
          <div className="flex flex-col items-center justify-center h-full py-10 border-2 border-dashed border-gray-300 rounded-lg hover:bg-gray-50 transition-colors relative">
            <input 
              type="file" 
              accept=".jpg,.jpeg,.png,.webp" 
              onChange={handleGenerate2D}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <Upload className="w-16 h-16 text-gray-400 mb-4" />
            <h3 className="text-xl font-medium text-gray-700">Upload your image</h3>
            <p className="text-gray-400 mt-2">Supports JPG, PNG, WEBP</p>
          </div>
        )}

        {/* --- STEP 2: 预览与编辑 --- */}
        {step === 2 && !showEditor && (
          <div className="flex flex-col h-full">
            <div className="flex flex-col md:flex-row gap-6 mb-6">
              {/* 原图 */}
              <div className="flex-1">
                <p className="text-sm text-gray-500 mb-2">Original</p>
                <div className="bg-gray-100 rounded-lg overflow-hidden aspect-square flex items-center justify-center">
                  <img src={images.original} alt="Original" className="max-w-full max-h-full object-contain" />
                </div>
              </div>
              
              {/* 箭头 */}
              <div className="flex items-center justify-center text-gray-300">
                <ArrowRight className="w-8 h-8 rotate-90 md:rotate-0" />
              </div>

              {/* 生成的2D图 */}
              <div className="flex-1">
                <p className="text-sm text-gray-500 mb-2">Generated Silhouette</p>
                <div className="bg-white border-2 border-blue-100 rounded-lg overflow-hidden aspect-square flex items-center justify-center shadow-sm">
                  {images.current2d ? (
                    <img 
                      src={`http://127.0.0.1:8000${images.current2d}`}
                      alt="2D Silhouette" 
                      className="max-w-full max-h-full object-contain" 
                    />
                  ) : (
                    <span className="text-gray-400">No image</span>
                  )}
                </div>
              </div>
            </div>

            {/* 操作区 */}
            <div className="mt-auto border-t pt-6">
              {/* 画图按钮 */}
              <div className="flex gap-2 mb-4">
                <button
                  onClick={() => setShowEditor(true)}
                  className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 flex items-center"
                >
                  <Edit3 className="w-4 h-4 mr-2" />
                  Draw on Image
                </button>
              </div>

              <label className="block text-sm font-medium text-gray-700 mb-2">Edit Instructions (Optional)</label>
              <div className="flex gap-2 mb-4">
                <input
                  type="text"
                  value={editPrompt}
                  onChange={(e) => setEditPrompt(e.target.value)}
                  placeholder="e.g., Make it smoother, remove the hole..."
                  className="flex-1 border rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                />
                <button 
                  onClick={handleEdit2D}
                  disabled={!editPrompt}
                  className="bg-gray-800 text-white px-4 py-2 rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
                >
                  <Edit3 className="w-4 h-4 mr-2" />
                  Edit
                </button>
              </div>

              <button 
                onClick={handleGenerate3D}
                className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 shadow-lg flex items-center justify-center transition-transform hover:scale-[1.01]"
              >
                <Box className="w-5 h-5 mr-2" />
                Looks Good! Generate 3D Model
              </button>
            </div>
          </div>
        )}

        {/* 画布编辑器 */}
        {step === 2 && showEditor && (
          <ImageEditor
            imageUrl={`http://127.0.0.1:8000${images.current2d}`}  // 传递完整 URL
            onSave={handleEditorSave}
            onCancel={() => setShowEditor(false)}
          />
        )}

        {/* --- STEP 3: 结果展示 --- */}
        {step === 3 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="bg-green-100 p-4 rounded-full mb-4">
              <Box className="w-12 h-12 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">3D Model Ready!</h2>
            <p className="text-gray-500 mb-8">Your keychain model has been successfully generated.</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 w-full mb-8">
              <div className="border rounded-lg p-2 bg-gray-50">
                <p className="text-xs text-gray-400 mb-2 text-left">Rendering Preview</p>
                {result3D.previewUrl ? (
                  <img src={result3D.previewUrl} alt="3D Render" className="w-full h-48 object-contain" />
                ) : (
                  <div className="h-48 flex items-center justify-center text-gray-400">No Preview</div>
                )}
              </div>
              
              <div className="flex flex-col justify-center space-y-4">
                <button
                  onClick={handleDownloadSTL}
                  disabled={!result3D.stlUrl}
                  className={`px-6 py-3 rounded-lg flex items-center justify-center w-full ${
                    result3D.stlUrl 
                      ? 'bg-blue-600 hover:bg-blue-700 text-white cursor-pointer' 
                      : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  <Download className="w-5 h-5 mr-2" />
                  Download STL File
                </button>
                
                <button 
                  onClick={() => { setStep(1); setImages({}); setSessionId(''); }}
                  className="text-gray-500 hover:text-gray-700 underline text-sm"
                >
                  Start New Project
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;