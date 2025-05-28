# cython: language_level=3
import uuid
import json
import os
from datetime import datetime
from flask import render_template, request
from src.models import TranscriptEntry, db
from transmeet import generate_mind_map_from_transcript
from transmeet.utils.general_utils import get_logger

logger = get_logger(__name__)

from . import audio_bp

def generate_id():
    """Generate a short UUID for node identification"""
    return str(uuid.uuid4())[:8]

def load_mindmap(file_path):
    """Load mind map data from JSON file with error handling"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            logger.warning(f"Mind map file not found: {file_path}")
            # Return a default empty mind map
            return {"Root Topic": "New Mind Map"}
    except Exception as e:
        logger.error(f"Error loading mind map data: {e}")
        return {"Root Topic": "Error Loading Mind Map"}

def convert_to_jsmind(data):
    """Convert dictionary data structure to jsMind format with metadata and styling"""
    root_id = generate_id()

    # check if there is a root topic, if not, check if there is only one key and all there are subtopics
    if "Root Topic" not in data:
        if len(data) == 1 and isinstance(list(data.values())[0], dict):
            data["Root Topic"] = list(data.keys())[0]
            # make the subtopic at same level as the root topic
            data[data["Root Topic"]] = data.pop(list(data.keys())[0])
        else:
            data["Root Topic"] = "Mind Map"

    
    # Create the base jsMind structure
    jsmind = {
        "meta": {
            "name": data.get("Root Topic", "Mind Map"),
            "author": "TransMeet",
            "version": "1.0",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "format": "node_array",
        "data": [
            {
                "id": root_id, 
                "isroot": True, 
                "topic": data.get("Root Topic", "Mind Map"),
                "direction": "right",
                "expanded": True,
                "background-color": "#2563eb",
                "foreground-color": "#ffffff"
            }
        ]
    }
    
    # Colors for different levels
    level_colors = [
        {"bg": "#06b6d4", "fg": "#ffffff"},  # Level 1
        {"bg": "#0ea5e9", "fg": "#ffffff"},  # Level 2
        {"bg": "#3b82f6", "fg": "#ffffff"},  # Level 3
        {"bg": "#6366f1", "fg": "#ffffff"},  # Level 4
        {"bg": "#8b5cf6", "fg": "#ffffff"},  # Level 5
    ]
    
    def add_nodes(parent_id, children, level=0):
        """Recursively add nodes to the jsMind structure with styling based on level"""
        if not isinstance(children, dict):
            return
        
        for k, v in children.items():
            if k == "Root Topic":
                continue
                
            child_id = generate_id()
            color_index = min(level, len(level_colors)-1)
            
            # Create node with styling
            node = {
                "id": child_id, 
                "parentid": parent_id, 
                "topic": k,
                "expanded": False,  # Default to collapsed
                "background-color": level_colors[color_index]["bg"],
                "foreground-color": level_colors[color_index]["fg"]
            }
            
            # Add direction to first-level nodes
            if level == 0:
                # Alternate left/right for better layout
                direction = "right" if len(jsmind["data"]) % 2 == 0 else "left"
                node["direction"] = direction
                
            jsmind["data"].append(node)
            
            if isinstance(v, dict):
                add_nodes(child_id, v, level + 1)
            elif isinstance(v, list):
                for item in v:
                    leaf_id = generate_id()
                    leaf_color_index = min(level + 1, len(level_colors)-1)
                    jsmind["data"].append({
                        "id": leaf_id, 
                        "parentid": child_id, 
                        "topic": item,
                        "background-color": level_colors[leaf_color_index]["bg"],
                        "foreground-color": level_colors[leaf_color_index]["fg"]
                    })
    
    add_nodes(root_id, data)
    return jsmind


@audio_bp.route("/mindmap", methods=["GET"])
def mindmap():
    """Main page route"""
    file_id = request.args.get("id")  # Get ID from query string
    
    if not file_id:
        return "Missing 'id' parameter in request", 400

    file_record = TranscriptEntry.query.filter_by(id=file_id).first()
    
    if not file_record:
        return f"No record found for id: {file_id}", 404

    if file_record.mind_map:
        # Load mind map from JSON
        mindmap_data = file_record.mind_map
        jsmind_data = convert_to_jsmind(mindmap_data)
        filename = file_record.filename
        
        root_title = jsmind_data.get("meta", {}).get("name", "Mind Map")

        return render_template("mindmap.html", 
                               jsmind_data=json.dumps(jsmind_data),
                               map_title=root_title,
                               filename=filename,
                               creator_name = jsmind_data.get("meta", {}).get("author", "unknown"),
                               creation_date = jsmind_data.get("meta", {}).get("created_at", "unknown"),
        )
    else:
        transcript = file_record.transcript

        mindmap_data = generate_mind_map_from_transcript(
            transcript,
            llm_client=file_record.llm_client,
            llm_model=file_record.llm_model
        )
        file_record.mind_map = mindmap_data
        file_record.status = "completed"
        file_record.completion_time = datetime.utcnow()
        db.session.commit()
        

        jsmind_data = convert_to_jsmind(mindmap_data)
        root_title = jsmind_data.get("meta", {}).get("name", "Mind Map")
        return render_template("mindmap.html", 
                               jsmind_data=json.dumps(jsmind_data),
                                 map_title=root_title,
                                 filename=file_record.filename,
                                    creator_name = jsmind_data.get("meta", {}).get("author", "unknown"),
                                    creation_date = jsmind_data.get("meta", {}).get("created_at", "unknown"),
        )
