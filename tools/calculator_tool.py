# ============================================
# tools/calculator_tool.py
# Agricultural calculator for yield, fertilizer, pesticide dosage
# ============================================

from langchain_core.tools import tool


@tool
def agri_calculator(
    operation: str,
    value_a: float,
    value_b: float
) -> dict:
    """
    Perform agricultural calculations.
    Operations:
      - 'add'        : value_a + value_b
      - 'subtract'   : value_a - value_b
      - 'multiply'   : value_a * value_b (e.g., area * yield_per_acre)
      - 'divide'     : value_a / value_b (e.g., total_cost / area)
      - 'percentage' : value_a % of value_b  (e.g., loss % of harvest)
    
    Examples:
      - Crop yield: operation='multiply', value_a=5 (acres), value_b=30 (maunds/acre)
      - Fertilizer per acre: operation='divide', value_a=100 (kg total), value_b=5 (acres)
      - Profit margin: operation='percentage', value_a=20 (profit), value_b=100 (revenue)
    """
    try:
        op = operation.lower().strip()
        if op == "add":
            result = value_a + value_b
        elif op in ("subtract", "sub"):
            result = value_a - value_b
        elif op in ("multiply", "mul"):
            result = value_a * value_b
        elif op in ("divide", "div"):
            if value_b == 0:
                return {"error": "Cannot divide by zero"}
            result = value_a / value_b
        elif op in ("percentage", "percent", "%"):
            if value_b == 0:
                return {"error": "Cannot compute percentage with zero base"}
            result = (value_a / value_b) * 100
        else:
            return {"error": f"Unknown operation '{operation}'. Use: add, subtract, multiply, divide, percentage"}
        
        return {
            "operation": operation,
            "value_a": value_a,
            "value_b": value_b,
            "result": round(result, 4)
        }
    except Exception as e:
        return {"error": str(e)}
