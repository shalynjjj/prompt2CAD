import io
import base64
import os

import numpy as np
from stl import mesh
from PIL import Image
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

class Model3DService:
    """Handles 3D model generation."""
    def generate_stl_from_2d(self, silhouette_path: str, proportions: dict) -> bytes:

        try:
            print("starting STL generation from 2D silhouette. ")
            print(f"silhouette path: {silhouette_path}")

            img=Image.open(silhouette_path).convert('L')

            max_size=512
            img.thumbnail((max_size,max_size),Image.Resampling.LANCZOS)

            img_array=np.array(img)
            print("generating STL from silhouette at:",silhouette_path)

            binary_img=(img_array>128).astype(int)
            thickness=proportions.get('thickness',0.3)*10
            print("using thickness:",thickness)

            vertices,faces=self._extrude_to_3d(binary_img,thickness)
            print("vertices and faces generated:",vertices.shape,faces.shape)

            stl_mesh=mesh.Mesh(np.zeros(faces.shape[0],dtype=mesh.Mesh.dtype))
            for i,face in enumerate(faces):
                for j in range(3):
                    stl_mesh.vectors[i][j]=vertices[face[j],:]
            
            buffer=io.BytesIO()
            stl_mesh.save('temp',fh=buffer)
            buffer.seek(0)
            stl_bytes=buffer.getvalue()

            print("STL generation completed.")
            return stl_bytes
        except Exception as e:
            raise ValueError(f"STL generation failed: {str(e)}")

    def _extrude_to_3d(self, binary_image, thickness):
        height, width = binary_image.shape
        
        # 找到所有非零像素的坐标
        y_coords, x_coords = np.where(binary_image > 0)
        
        if len(x_coords) == 0:
            raise ValueError("No non-zero pixels found in image")
        
        # 创建顶点（前表面和后表面）
        num_points = len(x_coords)
        print(f"📍 Found {num_points} non-zero pixels")
        
        # 采样（如果点太多）
        if num_points > 5000:
            step = num_points // 5000
            x_coords = x_coords[::step]
            y_coords = y_coords[::step]
            num_points = len(x_coords)
            print(f"⚡ Sampled to {num_points} points")
        
        # 前表面 (Z = 0)
        front = np.column_stack([
            x_coords,
            y_coords,
            np.zeros(num_points)
        ])
        # 后表面 (Z = thickness)
        back = np.column_stack([
            x_coords,
            y_coords,
            np.full(num_points, thickness)
        ])
        
        vertices = np.vstack([front, back]).astype(float)
        
        # 创建简单的三角形面（使用 Delaunay 三角剖分会更好，这里用简化版）
        faces = []
        
        # 只创建侧面连接（简化版）
        for i in range(num_points - 1):
            # 侧面的两个三角形
            faces.append([i, i+1, i + num_points])
            faces.append([i+1, i+1 + num_points, i + num_points])
        
        # 闭合循环
        faces.append([num_points-1, 0, num_points-1 + num_points])
        faces.append([0, num_points, num_points-1 + num_points])
        
        return vertices, np.array(faces)
   
    def generate_3d_render(self, stl_path: str) -> str:
        """Generate render preview, returns base64."""
        try:
            import matplotlib.pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            from stl import mesh
            import io
            import base64
            
            your_mesh = mesh.Mesh.from_file(stl_path)
            
            fig = plt.figure(figsize=(10, 10))
            ax = fig.add_subplot(111, projection='3d')
            ax.add_collection3d(Axes3D.art3d.Poly3DCollection(
                your_mesh.vectors, alpha=0.7, facecolor='cyan', edgecolor='black'
            ))
            
            scale = your_mesh.points.flatten()
            ax.auto_scale_xyz(scale, scale, scale)
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            render_b64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            return render_b64
        except Exception as e:
            raise ValueError(f"Render generation failed: {str(e)}")

    def render_stl_to_image(self, stl_path: str) -> str:
        """
        Render STL file to image preview.
        
        Args:
            stl_path: Path to the STL file
            
        Returns:
            Base64 encoded PNG image
        """
        try:
            print(f"=" * 80)
            print(f"🖼️ Rendering STL: {stl_path}")
            
            # Load mesh
            your_mesh = mesh.Mesh.from_file(stl_path)
            print(f"📊 Mesh loaded: {len(your_mesh.vectors)} triangles")
            
            # Create figure
            fig = plt.figure(figsize=(10, 10))
            ax = fig.add_subplot(111, projection='3d')
            
            # Add mesh to plot
            collection = Poly3DCollection(
                your_mesh.vectors, 
                alpha=0.7, 
                facecolor='cyan', 
                edgecolor='black',
                linewidths=0.5
            )
            ax.add_collection3d(collection)
            
            # Auto scale
            scale = your_mesh.points.flatten()
            ax.auto_scale_xyz(scale, scale, scale)
            
            # Set labels
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')
            ax.set_title('3D Model Preview')
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            render_b64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close(fig)
            
            print(f"✅ Render generated, base64 length: {len(render_b64)}")
            print(f"=" * 80)
            
            return render_b64
        except Exception as e:
            import traceback
            print(f"=" * 80)
            print(f"❌ ERROR in render_stl_to_image:")
            print(traceback.format_exc())
            print(f"=" * 80)
            raise ValueError(f"Render generation failed: {str(e)}")
        
Model3DService = Model3DService()