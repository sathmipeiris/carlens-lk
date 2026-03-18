import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
import argparse
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
import joblib

# ========================================
# 1. CUSTOM DATASET CLASS
# ========================================
class CarPriceDataset(Dataset):
    """PyTorch Dataset for car price prediction"""
    def __init__(self, X_numeric, X_brand, X_model, X_town, y):
        self.X_numeric = torch.FloatTensor(X_numeric)
        self.X_brand = torch.LongTensor(X_brand)
        self.X_model = torch.LongTensor(X_model)
        self.X_town = torch.LongTensor(X_town)
        self.y = torch.FloatTensor(y).unsqueeze(1)
    
    def __len__(self):
        return len(self.y)
    
    def __getitem__(self, idx):
        return (
            self.X_numeric[idx],
            self.X_brand[idx],
            self.X_model[idx],
            self.X_town[idx],
            self.y[idx]
        )

# ========================================
# 2. CUSTOM NEURAL NETWORK ARCHITECTURE
# ========================================
class CarPriceNet(nn.Module):
    """
    Custom Deep Learning Model for Car Price Prediction
    
    Architecture:
    - Embedding layers for categorical features (Brand, Model, Town)
    - Dense layers for numeric features
    - Attention mechanism to weight important features
    - Residual connections for better gradient flow
    - Batch normalization and dropout for regularization
    """
    def __init__(self, 
                 n_numeric_features,
                 n_brands, n_models, n_towns,
                 embedding_dim=16,
                 hidden_dims=[256, 128, 64],
                 dropout_rate=0.3):
        super(CarPriceNet, self).__init__()
        
        # ===== EMBEDDING LAYERS for high-cardinality categoricals =====
        self.brand_embedding = nn.Embedding(n_brands, embedding_dim)
        self.model_embedding = nn.Embedding(n_models, embedding_dim)
        self.town_embedding = nn.Embedding(n_towns, embedding_dim // 2)  # Town is less important
        
        # Total input size after concatenating embeddings + numeric
        total_input_dim = n_numeric_features + (embedding_dim * 2) + (embedding_dim // 2)
        
        # ===== NUMERIC FEATURE PROCESSING =====
        self.numeric_bn = nn.BatchNorm1d(n_numeric_features)
        
        # ===== ATTENTION MECHANISM (learn which features matter most) =====
        self.attention = nn.Sequential(
            nn.Linear(total_input_dim, total_input_dim // 2),
            nn.Tanh(),
            nn.Linear(total_input_dim // 2, total_input_dim),
            nn.Softmax(dim=1)
        )
        
        # ===== MAIN DENSE NETWORK with Residual Connections =====
        layers = []
        prev_dim = total_input_dim
        
        for i, hidden_dim in enumerate(hidden_dims):
            # Dense layer
            layers.append(nn.Linear(prev_dim, hidden_dim))
            layers.append(nn.BatchNorm1d(hidden_dim))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout_rate))
            
            # Residual connection (if dimensions match)
            if prev_dim == hidden_dim:
                self.add_residual = True
            else:
                self.add_residual = False
            
            prev_dim = hidden_dim
        
        self.dense_layers = nn.Sequential(*layers)
        
        # ===== OUTPUT LAYER =====
        self.output = nn.Sequential(
            nn.Linear(hidden_dims[-1], 32),
            nn.ReLU(),
            nn.Linear(32, 1)  # Single price prediction
        )
        
        # ===== INITIALIZE WEIGHTS =====
        self._init_weights()
    
    def _init_weights(self):
        """Xavier/He initialization for better convergence"""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.kaiming_normal_(m.weight, mode='fan_in', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Embedding):
                nn.init.normal_(m.weight, mean=0, std=0.01)
    
    def forward(self, x_numeric, x_brand, x_model, x_town):
        # ===== EMBED CATEGORICAL FEATURES =====
        brand_emb = self.brand_embedding(x_brand)     # (batch, embedding_dim)
        model_emb = self.model_embedding(x_model)     # (batch, embedding_dim)
        town_emb = self.town_embedding(x_town)        # (batch, embedding_dim // 2)
        
        # ===== NORMALIZE NUMERIC FEATURES =====
        x_numeric = self.numeric_bn(x_numeric)
        
        # ===== CONCATENATE ALL FEATURES =====
        x = torch.cat([x_numeric, brand_emb, model_emb, town_emb], dim=1)
        
        # ===== APPLY ATTENTION (learn feature importance dynamically) =====
        attention_weights = self.attention(x)
        x = x * attention_weights  # Weighted features
        
        # ===== PASS THROUGH DENSE LAYERS =====
        x = self.dense_layers(x)
        
        # ===== OUTPUT PRICE PREDICTION =====
        out = self.output(x)
        return out

# ========================================
# 3. TRAINING FUNCTION
# ========================================
def train_custom_model(model, train_loader, val_loader, epochs=100, lr=0.001, device='cpu'):
    """
    Train the custom neural network
    
    Uses:
    - Adam optimizer (adaptive learning rate)
    - Huber loss (robust to outliers - better than MSE for price prediction)
    - Learning rate scheduler (reduce on plateau)
    - Early stopping (prevent overfitting)
    """
    model = model.to(device)
    
    # Loss function: Huber is better than MSE for price prediction (robust to outliers)
    criterion = nn.HuberLoss(delta=5.0)  # Less sensitive to large errors
    
    # Optimizer with weight decay (L2 regularization)
    optimizer = optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    
    # Learning rate scheduler
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=5
    )
    
    # Early stopping
    best_val_loss = float('inf')
    patience_counter = 0
    patience = 10
    
    history = {'train_loss': [], 'val_loss': [], 'val_r2': []}
    
    for epoch in range(epochs):
        # ===== TRAINING PHASE =====
        model.train()
        train_losses = []
        
        for x_num, x_brand, x_model, x_town, y in train_loader:
            x_num = x_num.to(device)
            x_brand = x_brand.to(device)
            x_model = x_model.to(device)
            x_town = x_town.to(device)
            y = y.to(device)
            
            # Forward pass
            y_pred = model(x_num, x_brand, x_model, x_town)
            loss = criterion(y_pred, y)
            
            # Backward pass
            optimizer.zero_grad()
            loss.backward()
            
            # Gradient clipping (prevent exploding gradients)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            train_losses.append(loss.item())
        
        avg_train_loss = np.mean(train_losses)
        
        # ===== VALIDATION PHASE =====
        model.eval()
        val_losses = []
        all_preds = []
        all_targets = []
        
        with torch.no_grad():
            for x_num, x_brand, x_model, x_town, y in val_loader:
                x_num = x_num.to(device)
                x_brand = x_brand.to(device)
                x_model = x_model.to(device)
                x_town = x_town.to(device)
                y = y.to(device)
                
                y_pred = model(x_num, x_brand, x_model, x_town)
                loss = criterion(y_pred, y)
                val_losses.append(loss.item())
                
                all_preds.extend(y_pred.cpu().numpy())
                all_targets.extend(y.cpu().numpy())
        
        avg_val_loss = np.mean(val_losses)
        # Flatten collected predictions/targets to 1D arrays for sklearn metrics
        preds_arr = np.array(all_preds).ravel()
        targets_arr = np.array(all_targets).ravel()
        val_r2 = r2_score(targets_arr, preds_arr)

        # Update learning rate
        scheduler.step(avg_val_loss)

        # Early stopping check
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            # Save best model
            torch.save(model.state_dict(), 'best_custom_model.pth')
        else:
            patience_counter += 1

        history['train_loss'].append(avg_train_loss)
        history['val_loss'].append(avg_val_loss)
        history['val_r2'].append(val_r2)

        # Print progress
        if (epoch + 1) % 10 == 0:
            print(f"Epoch {epoch+1}/{epochs} | Train Loss: {avg_train_loss:.4f} | "
                  f"Val Loss: {avg_val_loss:.4f} | Val R²: {val_r2:.4f}")

        # Early stopping
        if patience_counter >= patience:
            print(f"Early stopping at epoch {epoch+1}")
            break
    
    # Load best model
    model.load_state_dict(torch.load('best_custom_model.pth'))
    return model, history

# ========================================
# 4. MAIN EXECUTION PIPELINE
# ========================================
def build_and_train_custom_model(X, y, le_brand, le_model, le_town, epochs=100, batch_size=64):
    """
    Complete pipeline to build and train custom model
    """
    # Ensure y is a 1D numpy array (preprocess_data may return pd.Series or np.array)
    y = np.asarray(y).ravel()
    # Separate numeric and categorical features
    categorical_cols = ['Brand_Encoded', 'Model_Encoded', 'Town_Encoded']
    numeric_cols = [col for col in X.columns if col not in categorical_cols]
    
    X_numeric = X[numeric_cols].values
    X_brand = X['Brand_Encoded'].values
    X_model = X['Model_Encoded'].values
    X_town = X['Town_Encoded'].values
    
    # Scale numeric features
    scaler = StandardScaler()
    X_numeric = scaler.fit_transform(X_numeric)
    
    # Train/val split
    (X_num_train, X_num_val,
     X_brand_train, X_brand_val,
     X_model_train, X_model_val,
     X_town_train, X_town_val,
     y_train, y_val) = train_test_split(
        X_numeric, X_brand, X_model, X_town, y,
        test_size=0.2, random_state=42
    )
    
    # Create datasets
    train_dataset = CarPriceDataset(X_num_train, X_brand_train, X_model_train, X_town_train, y_train)
    val_dataset = CarPriceDataset(X_num_val, X_brand_val, X_model_val, X_town_val, y_val)
    
    # Create dataloaders (batch_size controllable for smoke tests)
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # Initialize model
    n_brands = len(le_brand.classes_)
    n_models = len(le_model.classes_)
    n_towns = len(le_town.classes_)
    
    model = CarPriceNet(
        n_numeric_features=len(numeric_cols),
        n_brands=n_brands,
        n_models=n_models,
        n_towns=n_towns,
        embedding_dim=16,
        hidden_dims=[256, 128, 64],
        dropout_rate=0.3
    )
    
    print(f"Model architecture:\n{model}")
    print(f"\nTotal parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Train model
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"\nTraining on: {device}")
    
    model, history = train_custom_model(
        model, train_loader, val_loader,
        epochs=epochs, lr=0.001, device=device
    )
    
    # Final evaluation
    model.eval()
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for x_num, x_brand, x_model, x_town, y in val_loader:
            x_num = x_num.to(device)
            x_brand = x_brand.to(device)
            x_model = x_model.to(device)
            x_town = x_town.to(device)
            
            y_pred = model(x_num, x_brand, x_model, x_town)
            all_preds.extend(y_pred.cpu().numpy())
            all_targets.extend(y.cpu().numpy())
    
    # Calculate final metrics: ensure arrays are 1D
    preds_arr = np.array(all_preds).ravel()
    targets_arr = np.array(all_targets).ravel()

    r2 = r2_score(targets_arr, preds_arr)
    mae = mean_absolute_error(targets_arr, preds_arr)
    # Use sqrt(MSE) for RMSE for compatibility with older sklearn versions
    rmse = float(np.sqrt(mean_squared_error(targets_arr, preds_arr)))
    mape = mean_absolute_percentage_error(targets_arr, preds_arr) * 100
    
    print(f"\n{'='*60}")
    print(f"FINAL CUSTOM MODEL PERFORMANCE")
    print(f"{'='*60}")
    print(f"R² Score:  {r2:.4f} ({r2*100:.2f}%)")
    print(f"MAE:       {mae:.2f} Lakhs")
    print(f"RMSE:      {rmse:.2f} Lakhs")
    print(f"MAPE:      {mape:.2f}%")
    print(f"{'='*60}")
    
    # Save artifacts
    torch.save(model.state_dict(), 'custom_car_price_model.pth')
    joblib.dump(scaler, 'custom_model_scaler.pkl')
    print("\n✓ Model saved as: custom_car_price_model.pth")
    print("✓ Scaler saved as: custom_model_scaler.pkl")
    
    return model, scaler, history

# ========================================
# 5. USAGE EXAMPLE
# ========================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train custom car price model")
    parser.add_argument("--smoke", action="store_true", help="Run a quick smoke test (small subset, 1 epoch)")
    parser.add_argument("--sample-size", type=int, default=512, help="Number of rows to use in smoke test (default 512)")
    parser.add_argument("--epochs", type=int, default=None, help="Override number of epochs for full run")
    parser.add_argument("--batch-size", type=int, default=None, help="Override batch size for training")
    args = parser.parse_args()

    # Load your preprocessed data
    from preprocessing import preprocess_data

    X, y, le_brand, le_model, le_town = preprocess_data("car_price_dataset.csv")

    if args.smoke:
        # Subsample the dataset for a fast smoke test
        n = min(args.sample_size, len(X))
        print(f"[smoke] Using first {n} rows for smoke test, epochs=1, smaller batch size")
        X_sample = X.iloc[:n].copy()
        y_sample = np.array(y)[:n]
        epochs = 1
        batch_size = args.batch_size or 32

        model, scaler, history = build_and_train_custom_model(
            X_sample, y_sample, le_brand, le_model, le_town,
            epochs=epochs, batch_size=batch_size
        )
    else:
        # Full run (allow optional overrides)
        epochs = args.epochs if args.epochs is not None else 100
        batch_size = args.batch_size if args.batch_size is not None else 64
        model, scaler, history = build_and_train_custom_model(
            X, y, le_brand, le_model, le_town,
            epochs=epochs, batch_size=batch_size
        )

    print("\nCustom model training complete!")
