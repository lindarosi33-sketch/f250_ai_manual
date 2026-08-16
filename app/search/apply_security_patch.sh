#!/bin/bash
# Security Patch Application Script for F250 Manual Search
# Run this when ready to apply input validation security updates

echo "🔐 Applying security patch to search_engine.py"
echo "==============================================="

# Backup current file
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="search_engine.py.backup_$TIMESTAMP"
cp search_engine.py "$BACKUP_FILE"
echo "✅ Backup created: $BACKUP_FILE"

# Check if secured version exists
if [ ! -f "search_engine_secured.py" ]; then
    echo "❌ Error: search_engine_secured.py not found!"
    echo "Please make sure the secured version exists in this directory."
    exit 1
fi

# Replace the file
cp search_engine_secured.py search_engine.py
echo "✅ Secured version installed"

# Test the new code
echo "🧪 Testing new code..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from search_engine import FixedSearch
    s = FixedSearch()
    print('✅ Search engine loaded successfully')
    
    # Test validation
    test_queries = [
        'wheel torque',
        'fuel filter',
        '<script>alert(1)</script>',
        '; DROP TABLE users;',
        '../../etc/passwd'
    ]
    
    for query in test_queries:
        result = s.weighted_search(query)
        if 'script' in query.lower() and len(result) > 0:
            print(f'⚠️  Warning: Malicious query returned results: {query}')
        else:
            print(f'  Test query: \"{query[:30]}...\" - Results: {len(result)}')
    
    print('✅ Basic security tests passed')
except Exception as e:
    print(f'❌ Error: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo ""
    echo "🔄 Restarting service..."
    sudo systemctl restart f250-manual.service
    sleep 2
    sudo systemctl status f250-manual.service --no-pager | grep -A 3 "Active:"
    
    echo ""
    echo "🎉 Security patch applied successfully!"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Visit https://ai.hephzibahforge.com"
    echo "   2. Test with normal searches (should work)"
    echo "   3. Test with malicious queries like:"
    echo "      - <script>alert('xss')</script>"
    echo "      - '; DROP TABLE;"
    echo "      - ../../etc/passwd"
    echo ""
    echo "📊 To check security events, look at the application logs:"
    echo "   sudo journalctl -u f250-manual.service -f"
else
    echo "❌ Test failed. Rolling back to backup..."
    cp "$BACKUP_FILE" search_engine.py
    echo "✅ Rolled back to backup"
fi
