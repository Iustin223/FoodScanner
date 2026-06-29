import os

# Add all bundled NVIDIA bins to PATH before importing paddle
nvidia_base = r"c:\Users\Iustin\anaconda3\envs\PAD\lib\site-packages\nvidia"
for lib in ['cudnn', 'cublas', 'cuda_runtime', 'cufft', 'curand', 'cusolver', 'cusparse', 'nvjitlink']:
    bin_path = os.path.join(nvidia_base, lib, 'bin')
    if os.path.exists(bin_path):
        os.environ['PATH'] = bin_path + ';' + os.environ['PATH']
        print(f"Added: {bin_path}")

# Now try importing
import paddle
print(paddle.utils.run_check())