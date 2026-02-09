import os
import sys
import time
import pandas as pd
import tkinter as tk
from tkinter import filedialog
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

# --- 1. RESOURCE PATH HELPER ---
def resource_path(relative_path):
    """ 
    Get absolute path to resource. 
    Essential for PyInstaller to find models and csvs inside the .exe 
    """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- 2. SETUP & LOADING ---
def load_taxonomy_dictionary():
    """
    Loads your 'taxonomy_master.csv' into a Python dictionary.
    Expected CSV columns: 'Scientific Name', 'Order', 'Family', 'Genus'
    """
    print(">>> Loading Taxonomy Dictionary...")
    
    # Matches the path defined in your .spec file (assets folder)
    tax_path = resource_path(os.path.join("assets", "taxonomy_master.csv"))
    
    if not os.path.exists(tax_path):
        print(f"!!! WARNING: Taxonomy file not found at: {tax_path}")
        print("!!! Output will lack Order/Family/Genus data.")
        return {}

    try:
        # Load specific columns
        df = pd.read_csv(tax_path)
        # Normalize column names just in case (strip whitespace)
        df.columns = [c.strip() for c in df.columns]
        
        # Create a dictionary for instant lookup: 
        # Key: "Cardinalis cardinalis" -> Value: {'Order': '...', 'Family': '...'}
        tax_dict = df.set_index('Scientific Name')[['Order', 'Family', 'Genus']].to_dict('index')
        print(f">>> Taxonomy Loaded: {len(tax_dict)} species ready.")
        return tax_dict
    except Exception as e:
        print(f"!!! ERROR reading taxonomy CSV: {e}")
        return {}

def load_model():
    """Initializes the BirdNET Analyzer"""
    print(">>> Initializing BirdNET Model... (Please wait)")
    
    # Paths to the model files inside the bundle
    model_path = resource_path(os.path.join("models", "audio-model.tflite"))
    label_path = resource_path(os.path.join("models", "labels", "en_us.txt"))
    print(model_path)
    print(label_path)
    os.listdir()
    try:
        return Analyzer(
            classifier_model_path=model_path, 
            classifier_labels_path=label_path
        )
    except Exception as e:
        print(f"!!! CRITICAL ERROR: Could not load BirdNET model.\n{e}")
        input("Press Enter to exit...")
        sys.exit(1)

def extract_timestamp(filename):
    """
    Attempts to extract a timestamp from the filename.
    Customize this logic if your AudioMoth format differs.
    """
    try:
        # Standard AudioMoth format: 20240101_120000.WAV
        # Takes the last 15 characters before the powerbi
        # extension
        return filename[:-4][-15:] 
    except:
        return None

# --- 3. MAIN LOGIC ---
def main():
    print("==========================================")
    print("       BirdSight Analytics Engine         ")
    print("==========================================")

    # A. Folder Selection (Hidden Root Window)
    root = tk.Tk()
    root.withdraw()

    root.attributes('-topmost', True)

    root.update()
    
    print("\n[Action Required] Please select the folder containing your audio files...")
    folder_path = filedialog.askdirectory(title="Select Audio Folder")

    if not folder_path:
        print("No folder selected. Exiting.")
        time.sleep(1)
        sys.exit()

    # B. Scan for Files
    valid_exts = ('.wav', '.mp3', '.flac', '.WAV', '.MP3')
    files = [f for f in os.listdir(folder_path) if f.endswith(valid_exts)]
    
    if not files:
        print(f"!!! No valid audio files found in: {folder_path}")
        input("Press Enter to exit...")
        sys.exit()
    
    print(f"Found {len(files)} audio files.")

    # C. Prepare Engine
    tax_dict = load_taxonomy_dictionary()
    analyzer = load_model()
    
    all_results = []
    start_time = time.time()

    print("\n>>> Starting Analysis...")

    # D. Processing Loop
    for i, file in enumerate(files):
        print(f"[{i+1}/{len(files)}] Analyzing: {file}")
        
        full_path = os.path.join(folder_path, file)
        
        try:
            recording = Recording(analyzer, full_path, min_conf=0.1) # Capture everything, filter in PowerBI
            recording.analyze()
            
            for d in recording.detections:
                sci_name = d['scientific_name']

                if sci_name not in tax_dict:
                    continue
                
                if sci_name in tax_dict:
                    print(sci_name)
                    
                # TAXONOMY LOOKUP
                # Defaults to "Unknown" if species isn't in your CSV
                tax_info = tax_dict.get(sci_name, {"Order": "Unknown", "Family": "Unknown", "Genus": "Unknown"})

                all_results.append({
                    "Filename": file,
                    "Species": d['common_name'],
                    "Scientific Name": sci_name,
                    "Confidence": d['confidence'],
                    "Start Time": d['start_time'],
                    "End Time": d['end_time'],
                    "Duration": d['end_time'] - d['start_time'],
                    "Timestamp_Str": extract_timestamp(file),
                    # Merged Columns
                    "Order": tax_info['Order'],
                    "Family": tax_info['Family'],
                    "Genus": tax_info['Genus']
                })
        except Exception as e:
            print(f"   ! Error processing file: {e}")

    # E. Save Results
    print("\n>>> Saving Data...")
    
    if all_results:
        df = pd.DataFrame(all_results)
        
        # Attempt to create a real DateTime object for Power BI Time Intelligence
        df['Datetime'] = pd.to_datetime(df['Timestamp_Str'], format='%Y%m%d_%H%M%S', errors='coerce')
        
        output_file = os.path.join(folder_path, "bird_analysis_results.csv")
        df.to_csv(output_file, index=False)
        
        elapsed = time.time() - start_time
        print(f"\n✅ SUCCESS! Processed {len(files)} files in {elapsed:.1f} seconds.")
        print(f"📊 Results saved to: {output_file}")
        print("👉 You can now refresh your Power BI Dashboard.")
        
    else:
        print("\n⚠️ Analysis complete, but no birds were detected (or files were empty).")

    print("\n==========================================")
    input("Press Enter to close this window...")

if __name__ == "__main__":
    main()