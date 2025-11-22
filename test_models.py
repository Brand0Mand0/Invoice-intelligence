"""Test both NEAR AI models on sample invoices."""
import asyncio
import pdfplumber
from app.services.near_ai import NearAIService


async def test_model(model_name: str, pdf_path: str, invoice_name: str):
    """Test a specific model on an invoice."""
    print(f"\n{'='*60}")
    print(f"Testing {model_name} on {invoice_name}")
    print(f"{'='*60}")

    try:
        # Extract text from PDF
        pdf_text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pdf_text += page_text + "\n\n"

        if not pdf_text.strip():
            print("❌ No text extracted from PDF")
            return None

        print(f"✓ Extracted {len(pdf_text)} characters of text")

        # Create prompt
        prompt = f"""Extract invoice information from this text and return ONLY a valid JSON object with no additional text or markdown.

Invoice Text:
{pdf_text}

Return ONLY this JSON format (no explanations, no markdown):
{{
    "vendor": "vendor name here",
    "invoice_number": "invoice number or null",
    "date": "MM/DD/YYYY or null",
    "total_amount": 0.00,
    "line_items": []
}}

Extract:
- vendor: Company/business name from top of invoice
- invoice_number: Invoice/order/receipt number
- date: Date in MM/DD/YYYY format
- total_amount: Total amount as number
- line_items: Leave empty for now"""

        # Test the API call
        import httpx
        from app.core.config import get_settings

        settings = get_settings()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.NEAR_AI_BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.NEAR_AI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                }
            )

            print(f"Status Code: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ API Error: {response.text[:500]}")
                return None

            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()

            print(f"✅ Got response ({len(content)} chars)")
            print(f"\nResponse preview:")
            print(content[:300] + "..." if len(content) > 300 else content)

            # Try to parse JSON
            import json
            import re

            # Remove markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)

            # Extract JSON object if wrapped in text
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                content = json_match.group(0)

            extracted_data = json.loads(content)

            print(f"\n✅ Successfully parsed JSON:")
            print(f"  Vendor: {extracted_data.get('vendor')}")
            print(f"  Invoice #: {extracted_data.get('invoice_number')}")
            print(f"  Date: {extracted_data.get('date')}")
            print(f"  Amount: ${extracted_data.get('total_amount')}")

            return extracted_data

    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {str(e)}")
        return None


async def main():
    """Run tests on both models."""

    # Test files
    twitter_invoice = "/tmp/invoice_uploads/f3243b23-40d7-4b00-84a8-d3c9e7af7369_twitter_invoice.pdf"
    saje_invoice = "/tmp/invoice_uploads/304452e4-d4b6-4817-a00c-1b574a73cd1a_Saje Natural Wellness Order 5619624 EMV Receipt.pdf"

    models = [
        "deepseek-ai/DeepSeek-V3.1",
        "zai-org/GLM-4.6"
    ]

    invoices = [
        ("Twitter", twitter_invoice),
        ("Saje", saje_invoice)
    ]

    results = {}

    for model in models:
        results[model] = {}
        for invoice_name, invoice_path in invoices:
            result = await test_model(model, invoice_path, invoice_name)
            results[model][invoice_name] = result

    # Summary
    print(f"\n\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")

    for model in models:
        print(f"\n{model}:")
        for invoice_name in ["Twitter", "Saje"]:
            status = "✅ Success" if results[model][invoice_name] else "❌ Failed"
            print(f"  {invoice_name}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
