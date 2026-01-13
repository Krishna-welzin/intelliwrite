import os
import sys

# Get the absolute path of the current directory (api/)
current_dir = os.path.dirname(os.path.abspath(__file__))
# Get the root directory (parent of api/)
root_dir = os.path.dirname(current_dir)
# Get the aeo_blog_engine directory
aeo_dir = os.path.join(root_dir, 'aeo_blog_engine')

# Add paths to sys.path to support imports
# We need root_dir to import 'aeo_blog_engine' as a package
sys.path.append(root_dir)
# We need aeo_dir to support absolute imports like 'from services' inside api.py
sys.path.append(aeo_dir)

# Import the Flask app
from aeo_blog_engine.api import app