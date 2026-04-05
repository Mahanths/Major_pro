#!/usr/bin/env python3
"""
Complete Intrusion Detection Pipeline using CSE-CIC-IDS2018 Dataset
============================================================

This script implements a comprehensive machine learning pipeline for detecting
network intrusions in East-West traffic using the CSE-CIC-IDS2018 dataset.

Features:
- Loads multiple CSV files efficiently
- Cleans and preprocesses data
- Filters for East-West traffic (172.31.*.*)
- Encodes labels and features
- Trains RandomForestClassifier
- Evaluates model performance

Author: Network Security Team
Date: April 5, 2026
"""

import os
import pandas as pd
import numpy as np
import warnings
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
import sys

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# ============================================================================
# CONFIGURATION
# ============================================================================

# Directory containing CSV files
DATA_DIR = "data"

# Target labels to keep
TARGET_LABELS = ["BENIGN", "Bot", "Infiltration", "Brute Force"]

# East-West traffic prefix (internal network)
EAST_WEST_PREFIX = "172.31"

# Train/Test split ratio
TEST_SIZE = 0.2
RANDOM_STATE = 42

# Model parameters
N_ESTIMATORS = 100
MAX_DEPTH = 20
N_JOBS = -1  # Use all available cores
VERBOSE = 1

# ============================================================================
# COLOR CODES FOR OUTPUT
# ============================================================================

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_section(title):
    """Print formatted section header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}")
    print(f"{title:^70}")
    print(f"{'='*70}{Colors.END}\n")

def print_step(step_num, description):
    """Print step description"""
    print(f"{Colors.CYAN}[STEP {step_num}] {description}{Colors.END}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}✗ {message}{Colors.END}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {message}{Colors.END}")

def print_info(message):
    """Print info message"""
    print(f"{Colors.BLUE}ℹ {message}{Colors.END}")

def print_dataset_shape(df, label="Dataset shape"):
    """Print dataset shape in formatted way"""
    rows, cols = df.shape
    print(f"   {label}: {Colors.BOLD}{rows:,} rows{Colors.END} × {Colors.BOLD}{cols} columns{Colors.END}")

def print_separator():
    """Print visual separator"""
    print(f"{Colors.BLUE}{'-'*70}{Colors.END}")

# ============================================================================
# STEP 1: LOAD DATA
# ============================================================================

def load_data(data_dir=DATA_DIR):
    """
    Load all CSV files from the data directory.
    
    Parameters:
    -----------
    data_dir : str
        Directory containing CSV files
        
    Returns:
    --------
    pd.DataFrame
        Combined DataFrame from all CSV files
    """
    print_step(1, "Loading CSV files from directory")
    print(f"   Location: {Colors.BOLD}{data_dir}{Colors.END}")
    
    # Check if directory exists
    if not os.path.exists(data_dir):
        print_error(f"Directory '{data_dir}' not found!")
        print_info("Create a 'data' folder and place CSV files there.")
        sys.exit(1)
    
    # Find all CSV files
    csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    
    if not csv_files:
        print_error(f"No CSV files found in '{data_dir}'!")
        sys.exit(1)
    
    print_info(f"Found {len(csv_files)} CSV file(s):")
    for csv_file in csv_files:
        print(f"      • {csv_file}")
    
    # Load all CSV files with efficient memory handling
    dfs = []
    total_rows = 0
    
    for csv_file in csv_files:
        file_path = os.path.join(data_dir, csv_file)
        
        try:
            # Load with memory optimization
            print(f"\n   Loading: {Colors.BOLD}{csv_file}{Colors.END}...", end=" ", flush=True)
            
            df = pd.read_csv(
                file_path,
                low_memory=False,  # Allow mixed types
                dtype_backend='numpy_nullable'  # Use nullable dtypes for better handling
            )
            
            rows = len(df)
            total_rows += rows
            dfs.append(df)
            print(f"✓ ({rows:,} rows)")
            
        except Exception as e:
            print_error(f"Failed to load {csv_file}: {str(e)}")
            continue
    
    # Combine all DataFrames
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True, sort=False)
        print(f"\n   Total loaded: {Colors.BOLD}{total_rows:,}{Colors.END} rows")
        print_dataset_shape(combined_df, "Combined shape")
        print_success("Data loading completed")
        return combined_df
    else:
        print_error("No data could be loaded!")
        sys.exit(1)

# ============================================================================
# STEP 2: CLEAN DATA
# ============================================================================

def clean_data(df):
    """
    Clean the dataset by:
    - Stripping whitespace from column names
    - Removing NaN values
    - Removing infinite values
    
    Parameters:
    -----------
    df : pd.DataFrame
        Raw dataset
        
    Returns:
    --------
    pd.DataFrame
        Cleaned dataset
    """
    print_step(2, "Cleaning dataset")
    
    initial_rows = len(df)
    print_info(f"Initial shape: {initial_rows:,} rows")
    
    # Strip whitespace from column names
    print("   • Stripping column names...", end=" ", flush=True)
    df.columns = df.columns.str.strip()
    print("✓")
    print_info(f"Columns: {df.columns.tolist()}")
    
    # Display missing values before cleaning
    print("\n   Before cleaning:")
    nan_counts = df.isna().sum()
    nan_cols = nan_counts[nan_counts > 0]
    if len(nan_cols) > 0:
        print(f"      NaN values by column:")
        for col, count in nan_cols.items():
            pct = (count / len(df)) * 100
            print(f"         • {col}: {count:,} ({pct:.2f}%)")
    else:
        print("      • No NaN values found")
    
    # Remove NaN values
    print("\n   Removing NaN values...", end=" ", flush=True)
    df_clean = df.dropna()
    removed_nan = initial_rows - len(df_clean)
    print(f"✓ (removed {removed_nan:,} rows)")
    
    # Replace infinite values with NaN then drop
    print("   Replacing infinite values...", end=" ", flush=True)
    df_clean = df_clean.replace([np.inf, -np.inf], np.nan)
    df_clean = df_clean.dropna()
    removed_inf = len(df_clean) - (initial_rows - removed_nan)
    print(f"✓ (removed {removed_inf:,} rows)")
    
    print("\n   After cleaning:")
    print_dataset_shape(df_clean, "Shape")
    rows_removed = initial_rows - len(df_clean)
    pct_removed = (rows_removed / initial_rows) * 100
    print_info(f"Removed: {rows_removed:,} rows ({pct_removed:.2f}%)")
    
    print_success("Data cleaning completed")
    return df_clean

# ============================================================================
# STEP 3: FILTER EAST-WEST TRAFFIC
# ============================================================================

def filter_east_west_traffic(df, src_col="Src IP", dst_col="Dst IP", prefix=EAST_WEST_PREFIX):
    """
    Filter for East-West traffic (internal network communication).
    Keep only rows where both source and destination IPs start with prefix.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset with IP columns
    src_col : str
        Name of source IP column
    dst_col : str
        Name of destination IP column
    prefix : str
        IP prefix to filter by (e.g., "172.31")
        
    Returns:
    --------
    pd.DataFrame
        Filtered dataset
    """
    print_step(3, "Filtering for East-West traffic")
    
    initial_rows = len(df)
    print_info(f"Initial shape: {initial_rows:,} rows")
    print_info(f"Filtering for IPs starting with: {Colors.BOLD}{prefix}{Colors.END}")
    
    # Check if columns exist
    if src_col not in df.columns or dst_col not in df.columns:
        print_warning(f"IP columns not found. Available columns: {df.columns.tolist()}")
        print_warning("Continuing without IP filtering...")
        return df
    
    # Filter for East-West traffic
    mask = (df[src_col].astype(str).str.startswith(prefix)) & \
           (df[dst_col].astype(str).str.startswith(prefix))
    
    df_filtered = df[mask].copy()
    rows_removed = initial_rows - len(df_filtered)
    
    print(f"\n   • Rows with both IPs starting with {prefix}: {len(df_filtered):,}")
    print(f"   • Rows removed: {rows_removed:,}")
    pct_removed = (rows_removed / initial_rows) * 100
    print_info(f"Filtered out: {pct_removed:.2f}% of rows")
    
    print_dataset_shape(df_filtered, "After filtering")
    print_success("East-West traffic filtering completed")
    
    return df_filtered

# ============================================================================
# STEP 4: FILTER LABELS
# ============================================================================

def filter_labels(df, label_col="Label", target_labels=TARGET_LABELS):
    """
    Keep only rows with target labels.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset with label column
    label_col : str
        Name of label column
    target_labels : list
        List of labels to keep
        
    Returns:
    --------
    pd.DataFrame
        Filtered dataset
    """
    print_step(4, "Filtering labels")
    
    initial_rows = len(df)
    print_info(f"Initial shape: {initial_rows:,} rows")
    
    # Display current labels
    print("\n   Current label distribution:")
    label_counts = df[label_col].value_counts()
    for label, count in label_counts.items():
        pct = (count / len(df)) * 100
        print(f"      • {label}: {count:,} ({pct:.2f}%)")
    
    # Filter for target labels
    print(f"\n   Target labels: {Colors.BOLD}{target_labels}{Colors.END}")
    df_filtered = df[df[label_col].isin(target_labels)].copy()
    rows_removed = initial_rows - len(df_filtered)
    
    print(f"\n   • Rows kept: {len(df_filtered):,}")
    print(f"   • Rows removed: {rows_removed:,}")
    pct_removed = (rows_removed / initial_rows) * 100
    print_info(f"Removed: {pct_removed:.2f}% of rows")
    
    # Display new label distribution
    print("\n   After filtering:")
    new_label_counts = df_filtered[label_col].value_counts()
    for label, count in new_label_counts.items():
        pct = (count / len(df_filtered)) * 100
        print(f"      • {label}: {count:,} ({pct:.2f}%)")
    
    print_dataset_shape(df_filtered, "Shape")
    print_success("Label filtering completed")
    
    return df_filtered

# ============================================================================
# STEP 5: ENCODE LABELS
# ============================================================================

def encode_labels(df, label_col="Label"):
    """
    Encode categorical labels using LabelEncoder.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset with label column
    label_col : str
        Name of label column
        
    Returns:
    --------
    tuple
        (DataFrame with encoded labels, LabelEncoder)
    """
    print_step(5, "Encoding labels")
    
    df_encoded = df.copy()
    
    # Initialize and fit LabelEncoder
    le = LabelEncoder()
    df_encoded[label_col] = le.fit_transform(df[label_col])
    
    print("   Label mapping:")
    for idx, label in enumerate(le.classes_):
        print(f"      • {label}: {idx}")
    
    print_dataset_shape(df_encoded, "Shape after encoding")
    print_success("Label encoding completed")
    
    return df_encoded, le

# ============================================================================
# STEP 6: SELECT NUMERIC FEATURES
# ============================================================================

def select_numeric_features(df, label_col="Label"):
    """
    Keep only numeric features, excluding the label column.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Dataset with mixed types
    label_col : str
        Name of label column to exclude
        
    Returns:
    --------
    tuple
        (Feature DataFrame, Label Series)
    """
    print_step(6, "Selecting numeric features")
    
    initial_cols = len(df.columns)
    
    # Get numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove label column from features
    if label_col in numeric_cols:
        numeric_cols.remove(label_col)
    
    X = df[numeric_cols].copy()
    y = df[label_col].copy()
    
    print(f"   • Total columns: {initial_cols:,}")
    print(f"   • Numeric features: {len(numeric_cols):,}")
    print(f"   • Label column: {label_col}")
    
    print(f"\n   Features selected:")
    print(f"      {numeric_cols[:5]}...")  # Show first 5
    print(f"      (... and {len(numeric_cols)-5} more)")
    
    print(f"\n   • X shape: {X.shape}")
    print(f"   • y shape: {y.shape}")
    
    # Check for missing values
    X_nan = X.isna().sum().sum()
    if X_nan > 0:
        print_warning(f"Found {X_nan:,} NaN values in features - removing rows")
        X = X.dropna()
        y = y[X.index]
    
    print_success("Numeric feature selection completed")
    
    return X, y

# ============================================================================
# STEP 7: NORMALIZE FEATURES
# ============================================================================

def normalize_features(X_train, X_test):
    """
    Normalize features using StandardScaler.
    Fit scaler on training data, apply to both train and test.
    
    Parameters:
    -----------
    X_train : pd.DataFrame
        Training features
    X_test : pd.DataFrame
        Test features
        
    Returns:
    --------
    tuple
        (Normalized X_train, Normalized X_test, Scaler)
    """
    print_step(7, "Normalizing features")
    
    # Initialize scaler
    scaler = StandardScaler()
    
    print("   • Fitting scaler on training data...", end=" ", flush=True)
    scaler.fit(X_train)
    print("✓")
    
    # Transform both train and test
    print("   • Transforming training data...", end=" ", flush=True)
    X_train_scaled = scaler.transform(X_train)
    print("✓")
    
    print("   • Transforming test data...", end=" ", flush=True)
    X_test_scaled = scaler.transform(X_test)
    print("✓")
    
    # Show scaling statistics
    print("\n   Scaling statistics:")
    print(f"      • Mean (should be ~0): {np.mean(X_train_scaled):.6f}")
    print(f"      • Std (should be ~1): {np.std(X_train_scaled):.6f}")
    print(f"      • Min value: {np.min(X_train_scaled):.6f}")
    print(f"      • Max value: {np.max(X_train_scaled):.6f}")
    
    print(f"\n   • X_train scaled shape: {X_train_scaled.shape}")
    print(f"   • X_test scaled shape: {X_test_scaled.shape}")
    
    print_success("Feature normalization completed")
    
    return X_train_scaled, X_test_scaled, scaler

# ============================================================================
# STEP 8: SPLIT DATASET
# ============================================================================

def split_dataset(X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE):
    """
    Split dataset into train and test sets.
    
    Parameters:
    -----------
    X : pd.DataFrame or np.ndarray
        Features
    y : pd.Series or np.ndarray
        Labels
    test_size : float
        Proportion of test split (default 0.2 for 80/20)
    random_state : int
        Random seed for reproducibility
        
    Returns:
    --------
    tuple
        (X_train, X_test, y_train, y_test)
    """
    print_step(8, "Splitting dataset into train/test")
    
    total_samples = len(X)
    print_info(f"Total samples: {total_samples:,}")
    print_info(f"Split ratio: {1-test_size:.0%} train, {test_size:.0%} test")
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        stratify=y  # Maintain class distribution
    )
    
    print(f"\n   Training set:")
    print(f"      • X_train shape: {X_train.shape}")
    print(f"      • y_train shape: {y_train.shape}")
    print(f"      • Samples: {len(X_train):,} ({len(X_train)/total_samples*100:.1f}%)")
    
    print(f"\n   Test set:")
    print(f"      • X_test shape: {X_test.shape}")
    print(f"      • y_test shape: {y_test.shape}")
    print(f"      • Samples: {len(X_test):,} ({len(X_test)/total_samples*100:.1f}%)")
    
    # Display class distribution
    print(f"\n   Class distribution (train):")
    train_dist = pd.Series(y_train).value_counts().sort_index()
    for idx, count in train_dist.items():
        pct = count / len(y_train) * 100
        print(f"      • Class {idx}: {count:,} ({pct:.1f}%)")
    
    print_success("Dataset splitting completed")
    
    return X_train, X_test, y_train, y_test

# ============================================================================
# STEP 9: TRAIN MODEL
# ============================================================================

def train_model(X_train, y_train, n_estimators=N_ESTIMATORS, max_depth=MAX_DEPTH, random_state=RANDOM_STATE):
    """
    Train Random Forest Classifier.
    
    Parameters:
    -----------
    X_train : array-like
        Training features
    y_train : array-like
        Training labels
    n_estimators : int
        Number of trees in forest
    max_depth : int
        Maximum depth of trees
    random_state : int
        Random seed
        
    Returns:
    --------
    RandomForestClassifier
        Trained model
    """
    print_step(9, "Training Random Forest Classifier")
    
    print("   Model parameters:")
    print(f"      • n_estimators: {n_estimators}")
    print(f"      • max_depth: {max_depth}")
    print(f"      • n_jobs: {N_JOBS} (parallel processing)")
    
    # Initialize model
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
        n_jobs=N_JOBS,
        verbose=VERBOSE,
        class_weight='balanced'  # Handle class imbalance
    )
    
    print("\n   Training...", end=" ", flush=True)
    model.fit(X_train, y_train)
    print("✓")
    
    # Training predictions for cross-validation
    y_pred_train = model.predict(X_train)
    train_accuracy = accuracy_score(y_train, y_pred_train)
    
    print(f"\n   Training accuracy: {train_accuracy:.4f} ({train_accuracy*100:.2f}%)")
    print_success("Model training completed")
    
    return model

# ============================================================================
# STEP 10: EVALUATE MODEL
# ============================================================================

def evaluate_model(model, X_test, y_test, label_encoder=None):
    """
    Evaluate model performance on test set.
    
    Parameters:
    -----------
    model : RandomForestClassifier
        Trained model
    X_test : array-like
        Test features
    y_test : array-like
        Test labels
    label_encoder : LabelEncoder, optional
        For decoding labels
    """
    print_step(10, "Evaluating model performance")
    
    # Make predictions
    print("   Making predictions...", end=" ", flush=True)
    y_pred = model.predict(y_test)
    y_pred_proba = model.predict_proba(X_test)
    print("✓")
    
    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n   {Colors.BOLD}Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%){Colors.END}")
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print(f"\n   Confusion Matrix:")
    print(f"      {cm}")
    
    # Classification report
    print(f"\n   Classification Report:")
    print_separator()
    
    # Get class names if label encoder available
    if label_encoder is not None:
        target_names = label_encoder.classes_.tolist()
    else:
        target_names = None
    
    report = classification_report(
        y_test, y_pred,
        target_names=target_names,
        digits=4,
        zero_division=0
    )
    print(report)
    print_separator()
    
    # Feature importance
    print(f"\n   Top 10 Most Important Features:")
    feature_importance = pd.DataFrame({
        'feature': range(model.n_features_in_),
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False).head(10)
    
    for idx, row in feature_importance.iterrows():
        bar_length = int(row['importance'] * 50)
        bar = '█' * bar_length
        print(f"      Feature {int(row['feature']):3d}: {bar} {row['importance']:.4f}")
    
    print_success("Model evaluation completed")
    
    return {
        'accuracy': accuracy,
        'confusion_matrix': cm,
        'predictions': y_pred,
        'probabilities': y_pred_proba
    }

# ============================================================================
# MAIN PIPELINE
# ============================================================================

def main():
    """Main execution function"""
    
    # Print header
    print(f"\n{Colors.BOLD}{Colors.GREEN}")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  CSE-CIC-IDS2018 INTRUSION DETECTION PIPELINE".center(68) + "║")
    print("║" + "  East-West Traffic Analysis".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    print(f"{Colors.END}\n")
    
    try:
        # STEP 1: Load Data
        df = load_data()
        
        # STEP 2: Clean Data
        df = clean_data(df)
        
        # STEP 3: Filter East-West Traffic
        df = filter_east_west_traffic(df)
        
        # STEP 4: Filter Labels
        df = filter_labels(df)
        
        # STEP 5: Encode Labels
        df, label_encoder = encode_labels(df)
        
        # STEP 6: Select Numeric Features
        X, y = select_numeric_features(df)
        
        # STEP 8: Split Dataset (before normalization)
        X_train, X_test, y_train, y_test = split_dataset(X, y)
        
        # STEP 7: Normalize Features (after split)
        X_train_scaled, X_test_scaled, scaler = normalize_features(X_train, X_test)
        
        # STEP 9: Train Model
        model = train_model(X_train_scaled, y_train)
        
        # STEP 10: Evaluate Model
        results = evaluate_model(model, X_test_scaled, y_test, label_encoder)
        
        # Save artifacts
        print_section("Saving Model and Artifacts")
        
        print("   Saving model...", end=" ", flush=True)
        joblib.dump(model, 'ids_model.pkl')
        print("✓ (ids_model.pkl)")
        
        print("   Saving scaler...", end=" ", flush=True)
        joblib.dump(scaler, 'ids_scaler.pkl')
        print("✓ (ids_scaler.pkl)")
        
        print("   Saving label encoder...", end=" ", flush=True)
        joblib.dump(label_encoder, 'ids_label_encoder.pkl')
        print("✓ (ids_label_encoder.pkl)")
        
        # Final summary
        print_section("Pipeline Summary")
        print(f"   {Colors.GREEN}✓ Pipeline completed successfully!{Colors.END}")
        print(f"\n   Final Results:")
        print(f"      • Test Accuracy: {Colors.BOLD}{results['accuracy']:.4f}{Colors.END}")
        print(f"      • Model saved: ids_model.pkl")
        print(f"      • Scaler saved: ids_scaler.pkl")
        print(f"      • Label encoder saved: ids_label_encoder.pkl")
        print(f"\n   Ready for deployment or further analysis!")
        print()
        
    except Exception as e:
        print_section("Error")
        print_error(f"Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    main()
