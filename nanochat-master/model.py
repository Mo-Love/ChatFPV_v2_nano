import torch
import torch.nn as nn
import torch.nn.functional as F

class NanoGPT(nn.Module):
    def __init__(self, vocab_size, block_size, n_embd, n_head, n_layer):
        super().__init__()
        self.block_size = block_size
        self.tok_emb = nn.Embedding(vocab_size, n_embd)
        self.pos_emb = nn.Parameter(torch.zeros(1, block_size, n_embd))
        self.drop_emb = nn.Dropout(0.1)

        self.blocks = nn.Sequential(*[
            Block(n_embd, n_head) for _ in range(n_layer)
        ])
        self.ln_f = nn.LayerNorm(n_embd)
        self.head = nn.Linear(n_embd, vocab_size, bias=False)

        self.apply(self._init_weights)

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)
            if module.bias is not None:
                torch.nn.init.zeros_(module.bias)
        elif isinstance(module, nn.Embedding):
            torch.nn.init.normal_(module.weight, mean=0.0, std=0.02)

    def forward(self, idx, targets=None):
        B, T = idx.size()
        assert T <= self.block_size, f"Cannot forward sequence of length {T}, block size is {self.block_size}"
        assert idx.size(1) == T, f"Expected sequence length {T}, got {idx.size(1)}"

        token_embeddings = self.tok_emb(idx)  # each token in the sequence
        position_embeddings = self.pos_emb[:, :T, :]  # each position in the sequence
        x = token_embeddings + position_embeddings
        x = self.drop_emb(x)

        x = self.blocks(x)
        x = self.ln_f(x)
        logits = self.head(x)

        if targets is None:
            loss = None
        else:
            B, T, C = logits.size()
            logits = logits.view(B*T, C)
            targets = targets.view(B*T)
            loss = F.cross_entropy(logits, targets)

        return logits, loss
    def generate(self, prompt, max_length=500):
    # Токенізуй prompt
    tokens = tokenizer.encode(prompt)
    tokens = torch.tensor([tokens])
    with torch.no_grad():
        logits, _ = self(tokens)
    # Генерація (top-k sampling)
    for _ in range(max_length):
        logits = self(tokens[:, -1:, :])  # Останній токен
        probs = F.softmax(logits, dim=-1)
        next_token = torch.multinomial(probs, 1)
        tokens = torch.cat([tokens, next_token], dim=1)
    return tokenizer.decode(tokens[0].tolist())

class Block(nn.Module):
    def __init__(self, n_embd, n_head):
        super().__init__()
        head_size = n_embd // n_head
        self.sa = MultiHeadAttention(n_head, head_size)
        self.ffwd = FeedForward(n_embd)
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x):
        x = x + self.sa(self.ln1(x))
        x = x + self.ffwd(self.ln2(x))
        return x

class MultiHeadAttention(nn.Module):
    def __init__(self, num_heads, head_size):
        super().__init__()
        self.keys = nn.Linear(n_embd, num_heads * head_size)
        self.queries = nn.Linear(n_embd, num_heads * head_size)
        self.values = nn.Linear(n_embd, num_heads * head_size)
        self.proj = nn.Linear(num_heads * head_size, n_embd)
        self.dropout = nn.Dropout(0.1)

    def forward(self, x):
        B, T, C = x.size()
        k = self.keys(x).view(B, T, self.num_heads, self.head_size).transpose(1, 2)  # (B, nh, T, hs)
        q = self.queries(x).view(B, T, self.num_heads, self.head_size).transpose(1, 2)  # (B, nh, T, hs)
        v = self.values(x).view(B, T, self.num_heads, self.head_size).transpose(1, 2)  # (B, nh, T, hs)

        att = (q @ k.transpose(-2, -1)) * (1.0 / (self.head_size ** 0.5))
        att = F.softmax(att, dim=-1)
        att = self.dropout(att)
        y = att @ v  # (B, nh, T, hs)
        y = y.transpose(1, 2).contiguous().view(B, T, self.num_heads * self.head_size)  # (B, T, C)
        y = self.proj(y)
        return y

class FeedForward(nn.Module):
    def __init__(self, n_embd):
        super().__init__()
        self.c_fc = nn.Linear(n_embd, 4 * n_embd)
        self.c_proj = nn.Linear(4 * n_embd, n_embd)
        self.dropout = nn.Dropout(0.1)

    def forward(self, x):
        x = self.c_fc(x)
        x = F.gelu(x)
        x = self.c_proj(x)
        x = self.dropout(x)
        return x

# Hyperparameters
n_embd = 64
n_head = 4
n_layer = 2
block_size = 32
vocab_size = 50257  # GPT-2 vocab size

# Initialize model
model = NanoGPT(vocab_size, block_size, n_embd, n_head, n_layer)

# Dummy input for testing
dummy_input = torch.randint(0, vocab_size, (2, block_size))
logits, loss = model(dummy_input)
print("Logits shape:", logits.shape)
print("Loss:", loss.item())
