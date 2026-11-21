from app.analysis.ast_analyzer import ASTAnalyzer

def test_python_ast_extraction():
    code = """
import os
from math import sqrt

class Calculator:
    def add(self, a, b):
        return a + b

def calculate_payment(amount, currency='USD'):
    calc = Calculator()
    return calc.add(amount, 10)
"""
    result = ASTAnalyzer.analyze_python_code(code, "payment.py")
    assert len(result["classes"]) == 1
    assert result["classes"][0]["name"] == "Calculator"
    assert len(result["functions"]) == 2
    fn_names = [f["name"] for f in result["functions"]]
    assert "add" in fn_names
    assert "calculate_payment" in fn_names
    assert "math.sqrt" in result["imports"]

def test_polyglot_ts_extraction():
    ts_code = """
import { useState } from 'react';

export function calculateTotal(items: number[]): number {
    return items.reduce((a, b) => a + b, 0);
}
"""
    result = ASTAnalyzer.analyze_polyglot_code(ts_code, "total.ts")
    assert len(result["functions"]) >= 1
    assert result["functions"][0]["name"] == "calculateTotal"
    assert "react" in result["imports"]
