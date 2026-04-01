#!/bin/bash

while true; do
    echo "======================================"
    echo "🚀 START: $(date)"
    echo "======================================"

    # Step 1: Run proxy scraper
    echo "📡 [1/4] Scraping proxies..."
    cd /workspaces/codespaces-blank/proxy
    ./target/release/proxy-scraper-checker
    echo "✅ Scraping done!"

    # Step 2: Copy hasil scraper ke proxytester
    echo "📋 [2/4] Copying proxies to tester..."
    cp /workspaces/codespaces-blank/proxy/out/proxies/all.txt \
       /workspaces/codespaces-blank/proxytester/proxy.txt
    echo "✅ Copied! $(wc -l < /workspaces/codespaces-blank/proxytester/proxy.txt) proxies found"

    # Step 3: Run proxy tester
    echo "🧪 [3/4] Testing proxies..."
    cd /workspaces/codespaces-blank/proxytester
    go run main.go
    echo "✅ Testing done! $(wc -l < /workspaces/codespaces-blank/proxytester/good_proxy.txt) good proxies"

    # Step 4: Copy good proxy ke dawn & jalankan
    echo "🌅 [4/4] Copying good proxies to dawn & running..."
    cp /workspaces/codespaces-blank/proxytester/good_proxy.txt \
       /workspaces/codespaces-blank/dawn/proxy.txt
    cd /workspaces/codespaces-blank/dawn
    python main2.py &
    DAWN_PID=$!
    echo "✅ Dawn running with PID: $DAWN_PID"

    # Tunggu 3 jam
    echo "======================================"
    echo "⏳ Waiting 3 hours before restart..."
    echo "🔄 Next run: $(date -d '+3 hours')"
    echo "======================================"

    sleep 10800  # 3 jam = 10800 detik

    # Kill dawn sebelum restart
    echo "🛑 Stopping dawn (PID: $DAWN_PID)..."
    kill $DAWN_PID 2>/dev/null
    pkill -f "python main.py" 2>/dev/null

done
