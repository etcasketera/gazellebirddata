import tensorflow as tf
import tensorflow_hub as hub
import librosa
import numpy as np
import pandas as pd
import os

class PerchAnalyzer:
    def __init__(self, model_url="https://tfhub.dev/google/bird-vocalization-classifier/1"):
        self.model_url = model_url
        self.model = None
        self.labels = []
        self.sample_rate = 32000
        self.chunk_duration = 5.0 # seconds
        self.load_model()

    def load_model(self):
        print(f"Loading Perch model from {self.model_url}...")
        self.model = hub.load(self.model_url)
        self.infer_fn = self.model.signatures['serving_default']
        print("Model loaded.")
        self.load_labels()

    def load_labels(self):
        try:
            # Check for local labels file first
            local_labels = 'perch_labels.csv'
            if os.path.exists(local_labels):
                label_file = local_labels
            else:
                # Fallback: scan cache (less robust)
                cache_dir = os.environ.get('TFHUB_CACHE_DIR', '/tmp/tfhub_modules')
                label_file = None
                for root, dirs, files in os.walk(cache_dir):
                    if 'label.csv' in files:
                        path = os.path.join(root, 'label.csv')
                        try:
                            df = pd.read_csv(path)
                            if 'ebird2021' in df.columns:
                                label_file = path
                                break
                        except:
                            continue

            if label_file:
                df = pd.read_csv(label_file)
                # Use ebird2021 as the label
                self.labels = df['ebird2021'].tolist()
                print(f"Loaded {len(self.labels)} labels from {label_file}")
            else:
                print("Warning: Could not find label.csv. Labels will be indices.")
                self.labels = [str(i) for i in range(11000)] # Fallback

        except Exception as e:
            print(f"Error loading labels: {e}")
            self.labels = [str(i) for i in range(11000)]

    def analyze(self, file_path, min_conf=0.1, overlap=0.0):
        try:
            # Load audio
            sig, rate = librosa.load(file_path, sr=self.sample_rate, mono=True)
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return []

        chunk_samples = int(self.chunk_duration * self.sample_rate)
        step_samples = int(chunk_samples * (1 - overlap))

        # Split into chunks
        # We need to process in batches or loop.
        # For simplicity, loop or creating a large array.

        # Pad signal to ensure at least one chunk
        if len(sig) < chunk_samples:
            sig = np.pad(sig, (0, chunk_samples - len(sig)))

        chunks = []
        timestamps = [] # (start, end)

        for start_idx in range(0, len(sig) - chunk_samples + 1, step_samples):
            end_idx = start_idx + chunk_samples
            chunk = sig[start_idx:end_idx]
            chunks.append(chunk)
            timestamps.append((start_idx / self.sample_rate, end_idx / self.sample_rate))

        if not chunks:
            return []

        # Stack chunks
        batch = np.stack(chunks).astype(np.float32)

        # Run inference one by one as the model expects batch size 1
        results = []

        for i in range(len(batch)):
            chunk = batch[i] # (160000,)
            chunk_batch = chunk[np.newaxis, :] # (1, 160000)
            t_start, t_end = timestamps[i]

            # Inference
            outputs = self.infer_fn(inputs=tf.constant(chunk_batch))

            # output_0 is the logits
            logits = outputs['output_0'].numpy() # (1, 10932)
            probs = tf.nn.sigmoid(logits).numpy()[0] # (10932,)

            # Filter by confidence
            indices = np.where(probs >= min_conf)[0]

            for idx in indices:
                conf = float(probs[idx])
                label = self.labels[idx] if idx < len(self.labels) else str(idx)

                results.append({
                    'common_name': label, # Using ebird code as common name for now
                    'confidence': conf,
                    'start_time': t_start,
                    'end_time': t_end,
                    'label': label
                })

        return results
