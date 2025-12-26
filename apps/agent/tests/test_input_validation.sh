#!/bin/bash
# Test script for input validation

echo "Testing Input Validation"
echo "========================"
echo ""

# Test 1: Empty message (should fail with 422)
echo "Test 1: Empty message (should return 422)"
echo "------------------------------------------"
RESPONSE1=$(curl -X POST https://my-pmm-agent.vercel.app/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message":""}' \
     -w "\nHTTP_STATUS:%{http_code}" \
     -s)
HTTP_CODE1=$(echo "$RESPONSE1" | grep "HTTP_STATUS" | cut -d: -f2)
BODY1=$(echo "$RESPONSE1" | sed '/HTTP_STATUS/d')
echo "Response body:"
echo "$BODY1" | python3 -m json.tool 2>/dev/null || echo "$BODY1"
echo "HTTP Status: $HTTP_CODE1"
echo ""

# Test 2: Very long message (should fail with 422)
echo "Test 2: Very long message >50k chars (should return 422)"
echo "--------------------------------------------------------"
LONG_MSG=$(python3 -c "print('x' * 50001)")
RESPONSE2=$(curl -X POST https://my-pmm-agent.vercel.app/api/chat \
     -H "Content-Type: application/json" \
     -d "{\"message\":\"$LONG_MSG\"}" \
     -w "\nHTTP_STATUS:%{http_code}" \
     -s)
HTTP_CODE2=$(echo "$RESPONSE2" | grep "HTTP_STATUS" | cut -d: -f2)
BODY2=$(echo "$RESPONSE2" | sed '/HTTP_STATUS/d')
echo "Response body:"
echo "$BODY2" | python3 -m json.tool 2>/dev/null || echo "$BODY2"
echo "HTTP Status: $HTTP_CODE2"
echo ""

# Test 3: Valid message (should succeed with 200)
echo "Test 3: Valid message (should return 200)"
echo "------------------------------------------"
RESPONSE3=$(curl -X POST https://my-pmm-agent.vercel.app/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message":"Hello, this is a test"}' \
     -w "\nHTTP_STATUS:%{http_code}" \
     -s)
HTTP_CODE3=$(echo "$RESPONSE3" | grep "HTTP_STATUS" | cut -d: -f2)
BODY3=$(echo "$RESPONSE3" | sed '/HTTP_STATUS/d')
echo "Response body (first 200 chars):"
echo "$BODY3" | head -c 200
echo "..."
echo "HTTP Status: $HTTP_CODE3"
echo ""
