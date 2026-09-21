# GLM-4.6 API Secure Setup Guide

## 🎯 **Where to Put Your GLM-4.6 API Key**

### **Option 1: Local Environment File (Recommended for Development)**

Create a `.env.local` file in your project root:

```bash
# Navigate to your DMLogn8n directory
cd /home/activeloguser/DMLogn8n

# Create secure local environment file
touch .env.local
chmod 600 .env.local  # Only you can read/write
```

Add your API key to `.env.local`:

```bash
# GLM-4.6 Configuration
GLM4_API_KEY=your_actual_api_key_here
GLM4_ENDPOINT=https://open.bigmodel.cn/api/paas/v4/chat/completions
GLM4_MODEL=glm-4

# Additional security
GLM4_API_BASE64=$(echo -n "$GLM4_API_KEY" | base64)
```

### **Option 2: Environment Variables in Terminal**

Run this in a separate terminal before starting services:

```bash
# Terminal 1 - Set environment variables
export GLM4_API_KEY="your_actual_api_key_here"
export GLM4_ENDPOINT="https://open.bigmodel.cn/api/paas/v4/chat/completions"
export GLM4_MODEL="glm-4"

# Start the AI model pools service
cd /home/activeloguser/DMLogn8n
python multi-portal-gateway/services/ai_model_pools.py
```

### **Option 3: System Environment Variables (Permanent)**

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
# GLM-4.6 Configuration
export GLM4_API_KEY="your_actual_api_key_here"
export GLM4_ENDPOINT="https://open.bigmodel.cn/api/paas/v4/chat/completions"
export GLM4_MODEL="glm-4"
```

Then reload:
```bash
source ~/.bashrc  # or ~/.zshrc
```

### **Option 4: Docker Secrets (Production)**

Create a `secrets` directory:

```bash
mkdir -p secrets
echo "your_actual_api_key_here" > secrets/glm4_api_key
chmod 600 secrets/glm4_api_key
```

Update your `docker-compose.yml`:

```yaml
services:
  coder-bot:
    environment:
      - GLM4_API_KEY_FILE=/run/secrets/glm4_api_key
    secrets:
      - glm4_api_key

secrets:
  glm4_api_key:
    file: ./secrets/glm4_api_key
```

## 🚀 **Quick Start Commands**

### **Option A: Run Everything in One Terminal**

```bash
# 1. Set your API key
export GLM4_API_KEY="your_actual_api_key_here"

# 2. Run the complete setup script
chmod +x ./start-glm4-local.sh
./start-glm4-local.sh
```

### **Option B: Run Services in Separate Terminals**

**Terminal 1 - AI Model Pools:**
```bash
export GLM4_API_KEY="your_actual_api_key_here"
cd /home/activeloguser/DMLogn8n
python multi-portal-gateway/services/ai_model_pools.py
```

**Terminal 2 - Coder Bot:**
```bash
export GLM4_API_KEY="your_actual_api_key_here"
cd /home/activeloguser/DMLogn8n
python multi-portal-gateway/services/coder_bot.py
```

**Terminal 3 - Main Gateway:**
```bash
export GLM4_API_KEY="your_actual_api_key_here"
cd /home/activeloguser/DMLogn8n
python multi-portal-gateway/gateway/main.py
```

**Terminal 4 - AI Transparency:**
```bash
export GLM4_API_KEY="your_actual_api_key_here"
cd /home/activeloguser/DMLogn8n
python multi-portal-gateway/services/ai_transparency.py
```

## 🔐 **Security Best Practices**

1. **Never commit API keys to Git**
   ```bash
   # Add .env.local to .gitignore
   echo ".env.local" >> .gitignore
   echo "secrets/" >> .gitignore
   ```

2. **Use restrictive file permissions**
   ```bash
   chmod 600 .env.local  # Only owner can read/write
   ```

3. **Use different keys for development/production**
   - Development: Use a limited scope API key
   - Production: Use full scope key with monitoring

4. **Rotate keys regularly**
   - Change API keys every 30-90 days
   - Monitor key usage for anomalies

## 🧪 **Testing Your GLM-4.6 Connection**

Create a test script:

```python
# test_glm4.py
import asyncio
import aiohttp
import os

async def test_glm4():
    api_key = os.getenv("GLM4_API_KEY")
    if not api_key:
        print("❌ GLM4_API_KEY not set")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "glm-4",
        "messages": [{"role": "user", "content": "Say 'Hello from GLM-4!'" }],
        "temperature": 0.7,
        "max_tokens": 50
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://open.bigmodel.cn/api/paas/v4/chat/completions",
            json=payload,
            headers=headers
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                print("✅ GLM-4.6 is working!")
                print(f"Response: {data['choices'][0]['message']['content']}")
            else:
                print(f"❌ Error: {resp.status}")
                print(await resp.text())

if __name__ == "__main__":
    asyncio.run(test_glm4())
```

Run the test:
```bash
export GLM4_API_KEY="your_actual_api_key_here"
python test_glm4.py
```

## 📝 **Service Integration Points**

The GLM-4.6 API is used in these services:

1. **Coder Bot Service** (Port 7900)
   - Generates code modifications
   - Validates code safety
   - Reviews automated code

2. **AI Model Pools** (Background)
   - Medium-tier decisions (1-3s)
   - Tactical reasoning
   - Code generation tasks

3. **AI Transparency** (Port 3001)
   - Shows AI reasoning process
   - Logs decision paths
   - Provides audit trails

## 🚨 **Troubleshooting**

### **Common Issues:**

1. **API Key Not Working**
   - Verify key is correct and active
   - Check if you have sufficient credits
   - Ensure API endpoint is correct

2. **Connection Timeout**
   ```bash
   # Check network connectivity
   curl -I https://open.bigmodel.cn/api/paas/v4/chat/completions
   ```

3. **Environment Variables Not Loading**
   ```bash
   # Debug environment variables
   echo $GLM4_API_KEY
   env | grep GLM4
   ```

4. **Service Won't Start**
   ```bash
   # Check logs
   tail -f logs/coder-bot.log
   tail -f logs/ai-model-pools.log
   ```

## 🎯 **Next Steps**

1. Choose your preferred API key storage method
2. Set your GLM-4.6 API key
3. Run the test script to verify connection
4. Start the services using your preferred method
5. Access the services at their respective ports
6. Monitor logs for any issues

The system is designed to work with GLM-4.6 as the primary AI model for code generation and medium-complexity decisions, while using local models for fast responses and optionally other models (OpenAI/Anthropic) for complex strategic decisions.