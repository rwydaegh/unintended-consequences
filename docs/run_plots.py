import os
os.chdir('..')
os.system("python src/visualization/plots.py")
os.system("python src/analysis/ma_filter.py")