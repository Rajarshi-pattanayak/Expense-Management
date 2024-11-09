import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import json
from typing import Dict, List, Optional, Union
import calendar
from pathlib import Path
import pandas as pd

class ExpenseTracker:
    def __init__(self, data_file: str = "expenses.json"):
        """Initialize the expense tracker with a data file."""
        self.data_file = Path(data_file)
        self.data = self._load_data()
        
    def _load_data(self) -> Dict:
        """Load data from JSON file or create new structure if file doesn't exist."""
        if self.data_file.exists():
            with open(self.data_file, 'r') as f:
                return json.load(f)
        else:
            return {
                "expenses": [],
                "budgets": {
                    "total": 0,
                    "categories": {}
                }
            }
    
    def _save_data(self):
        """Save current data to JSON file."""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=4)
    
    def add_expense(self, amount: float, category: str, description: str, date: Optional[str] = None):
        """Add a new expense."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
            
        expense = {
            "date": date,
            "amount": float(amount),
            "category": category.lower(),
            "description": description
        }
        
        self.data["expenses"].append(expense)
        self._save_data()
        
        # Check budget after adding expense
        self._check_budget_alerts(expense)
    def delete_expense(self, date: str, amount: float, category: str, description: str):
        self.data["expenses"] = [
            expense for expense in self.data["expenses"]
            if not (
                expense["date"] == date
                and expense["amount"] == amount
                and expense["category"] == category
                and expense["description"] == description
            )
        ]
        self._save_data()

    def delete_budget(self, category: Optional[str] = None):
        """Delete a budget for a category or total budget."""
        if category:
            if category in self.data["budgets"]["categories"]:
                del self.data["budgets"]["categories"][category]
        else:
            self.data["budgets"]["total"] = 0
        self._save_data()
    
    def set_budget(self, amount: float, category: Optional[str] = None):
        """Set budget for a category or total budget."""
        if category:
            self.data["budgets"]["categories"][category.lower()] = float(amount)
        else:
            self.data["budgets"]["total"] = float(amount)
        self._save_data()
    
    def _check_budget_alerts(self, new_expense: Dict) -> List[str]:
        """Check if the new expense triggers any budget alerts."""
        alerts = []
        current_month = datetime.now().strftime("%Y-%m")
        
        # Check category budget
        category = new_expense["category"]
        if category in self.data["budgets"]["categories"]:
            monthly_category_spending = self.get_monthly_spending(current_month, category)
            category_budget = self.data["budgets"]["categories"][category]
            
            if monthly_category_spending >= category_budget:
                alerts.append(f"ALERT: You've exceeded your budget for {category}!")
            elif monthly_category_spending >= category_budget * 0.8:
                alerts.append(f"WARNING: You've used 80% of your budget for {category}!")
        
        # Check total budget
        if self.data["budgets"]["total"] > 0:
            monthly_total = self.get_monthly_spending(current_month)
            total_budget = self.data["budgets"]["total"]
            
            if monthly_total >= total_budget:
                alerts.append("ALERT: You've exceeded your total monthly budget!")
            elif monthly_total >= total_budget * 0.8:
                alerts.append("WARNING: You've used 80% of your total monthly budget!")
                
        return alerts
    
    def get_monthly_spending(self, month: str, category: Optional[str] = None) -> float:
        """Calculate total spending for a given month."""
        expenses = [
            expense for expense in self.data["expenses"]
            if expense["date"].startswith(month)
            and (category is None or expense["category"] == category)
        ]
        return sum(expense["amount"] for expense in expenses)
    
    def get_spending_by_category(self, month: Optional[str] = None) -> Dict[str, float]:
        """Get spending breakdown by category for a given month or all time."""
        expenses = self.data["expenses"]
        if month:
            expenses = [e for e in expenses if e["date"].startswith(month)]
            
        categories = {}
        for expense in expenses:
            cat = expense["category"]
            categories[cat] = categories.get(cat, 0) + expense["amount"]
        return categories
    
    def get_expense_summary(self, month: Optional[str] = None) -> Dict:
        """Generate a summary of expenses and budget status."""
        if month is None:
            month = datetime.now().strftime("%Y-%m")
            
        total_spent = self.get_monthly_spending(month)
        category_spending = self.get_spending_by_category(month)
        
        summary = {
            "total_spent": total_spent,
            "total_budget": self.data["budgets"]["total"],
            "budget_remaining": self.data["budgets"]["total"] - total_spent if self.data["budgets"]["total"] > 0 else None,
            "categories": {}
        }
        
        for category, spent in category_spending.items():
            budget = self.data["budgets"]["categories"].get(category, 0)
            summary["categories"][category] = {
                "spent": spent,
                "budget": budget,
                "remaining": budget - spent if budget > 0 else None
            }
            
        return summary

class ExpenseTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1920x1200")
        
        # Initialize expense tracker backend
        self.tracker = ExpenseTracker()
        
        # Create main container
        self.main_container = ttk.Notebook(self.root)
        self.main_container.pack(expand=True, fill="both", padx=10, pady=5)
        
        # Create tabs
        self.expenses_tab = ttk.Frame(self.main_container)
        self.budget_tab = ttk.Frame(self.main_container)
        self.analysis_tab = ttk.Frame(self.main_container)
        
        self.main_container.add(self.expenses_tab, text="Expenses")
        self.main_container.add(self.budget_tab, text="Budgets")
        self.main_container.add(self.analysis_tab, text="Analysis")
        
        self._setup_expenses_tab()
        self._setup_budget_tab()
        self._setup_analysis_tab()
        
    def _setup_expenses_tab(self):
        # Left side - Add Expense Form
        form_frame = ttk.LabelFrame(self.expenses_tab, text="Add New Expense", padding="10")
        form_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        
        # Amount
        ttk.Label(form_frame, text="Amount:").grid(row=0, column=0, padx=5, pady=5)
        self.amount_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.amount_var).grid(row=0, column=1, padx=5, pady=5)
        
        # Category
        ttk.Label(form_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(form_frame, textvariable=self.category_var)
        self.category_combo['values'] = ['Food', 'Transportation', 'Entertainment', 'Utilities', 'Shopping', 'Other']
        self.category_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Description
        ttk.Label(form_frame, text="Description:").grid(row=2, column=0, padx=5, pady=5)
        self.description_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.description_var).grid(row=2, column=1, padx=5, pady=5)
        
        # Date
        ttk.Label(form_frame, text="Date:").grid(row=3, column=0, padx=5, pady=5)
        self.date_entry = DateEntry(form_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2)
        self.date_entry.grid(row=3, column=1, padx=5, pady=5)
        
        # Add Button
        ttk.Button(form_frame, text="Add Expense", command=self._add_expense).grid(row=4, column=0, columnspan=2, pady=10)
        
        # Right side - Expense List
        list_frame = ttk.LabelFrame(self.expenses_tab, text="Recent Expenses", padding="10")
        list_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        
        # Treeview for expenses
        columns = ('Date', 'Category', 'Amount', 'Description')
        self.expense_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        # Set column headings
        for col in columns:
            self.expense_tree.heading(col, text=col)
            self.expense_tree.column(col, width=100)
        
        self.expense_tree.grid(row=0, column=0, sticky="nsew")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.expense_tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.expense_tree.configure(yscrollcommand=scrollbar.set)
        
        # Configure grid weights
        self.expenses_tab.grid_columnconfigure(1, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        ttk.Button(list_frame, text="Delete Selected Expense", 
          command=self._delete_selected_expense).grid(row=1, column=0, pady=5)
        
        self._refresh_expense_list()
        
    def _setup_budget_tab(self):
        # Budget Setting Form
        form_frame = ttk.LabelFrame(self.budget_tab, text="Set Budget", padding="10")
        form_frame.pack(fill="x", padx=10, pady=5)
        
        # Total Budget
        ttk.Label(form_frame, text="Total Monthly Budget:").grid(row=0, column=0, padx=5, pady=5)
        self.total_budget_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.total_budget_var).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(form_frame, text="Set Total Budget", 
                  command=lambda: self._set_budget(None)).grid(row=0, column=2, padx=5, pady=5)
        
        # Category Budget
        ttk.Label(form_frame, text="Category:").grid(row=1, column=0, padx=5, pady=5)
        self.budget_category_var = tk.StringVar()
        category_combo = ttk.Combobox(form_frame, textvariable=self.budget_category_var)
        category_combo['values'] = ['Food', 'Transportation', 'Entertainment', 'Utilities', 'Shopping', 'Other']
        category_combo.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Amount:").grid(row=2, column=0, padx=5, pady=5)
        self.category_budget_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.category_budget_var).grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(form_frame, text="Set Category Budget",
                  command=self._set_category_budget).grid(row=2, column=2, padx=5, pady=5)
        
        # Budget Overview
        overview_frame = ttk.LabelFrame(self.budget_tab, text="Budget Overview", padding="10")
        overview_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview for budget overview
        columns = ('Category', 'Budget', 'Spent', 'Remaining')
        self.budget_tree = ttk.Treeview(overview_frame, columns=columns, show='headings')

        ttk.Button(overview_frame, text="Delete Selected Budget",
          command=self._delete_selected_budget).pack(pady=5)
        
        for col in columns:
            self.budget_tree.heading(col, text=col)
            self.budget_tree.column(col, width=100)
        
        self.budget_tree.pack(fill="both", expand=True)
        self._refresh_budget_overview()
        
    def _setup_analysis_tab(self):
        # Create frames for charts
        charts_frame = ttk.Frame(self.analysis_tab)
        charts_frame.pack(fill="both", expand=True)
        
        # Split into left and right frames
        left_frame = ttk.LabelFrame(charts_frame, text="Monthly Spending Trend")
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        right_frame = ttk.LabelFrame(charts_frame, text="Category Breakdown")
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Configure grid weights
        charts_frame.grid_columnconfigure(0, weight=1)
        charts_frame.grid_columnconfigure(1, weight=1)
        
        # Add refresh button
        ttk.Button(self.analysis_tab, text="Refresh Charts", 
                  command=self._refresh_charts).pack(pady=5)
        
        self._refresh_charts()
        
    def _add_expense(self):
        try:
            amount = float(self.amount_var.get())
            category = self.category_var.get()
            description = self.description_var.get()
            date = self.date_entry.get_date().strftime("%Y-%m-%d")
            
            if not category or not description:
                messagebox.showerror("Error", "Please fill all fields")
                return
                
            self.tracker.add_expense(amount, category, description, date)
            
            # Clear form
            self.amount_var.set("")
            self.category_var.set("")
            self.description_var.set("")
            
            self._refresh_expense_list()
            self._refresh_budget_overview()
            messagebox.showinfo("Success", "Expense added successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
            
    def _refresh_expense_list(self):
        # Clear current items
        for item in self.expense_tree.get_children():
            self.expense_tree.delete(item)
            
        # Add expenses from tracker
        for expense in reversed(self.tracker.data["expenses"]):
            self.expense_tree.insert('', 'end', values=(
                expense["date"],
                expense["category"],
                f"${expense['amount']:.2f}",
                expense["description"]
            ))
    def _delete_selected_expense(self):
        selected_item = self.expense_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an expense to delete")
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this expense?"):
            item = self.expense_tree.item(selected_item[0])
            values = item['values']
            # Convert the amount string back to float (remove '$' and convert)
            amount = float(values[2].replace('$', ''))
            self.tracker.delete_expense(values[0], amount, values[1], values[3])
            self._refresh_expense_list()
            self._refresh_budget_overview()
            messagebox.showinfo("Success", "Expense deleted successfully!")

    def _delete_selected_budget(self):
        selected_item = self.budget_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a budget to delete")
            return
            
        if messagebox.askyesno("Confirm", "Are you sure you want to delete this budget?"):
            item = self.budget_tree.item(selected_item[0])
            category = item['values'][0]
            if category == 'Total':
                self.tracker.delete_budget()
            else:
                self.tracker.delete_budget(category)
            self._refresh_budget_overview()
            messagebox.showinfo("Success", "Budget deleted successfully!")
            
    def _set_budget(self, category: Optional[str] = None):
        try:
            amount = float(self.total_budget_var.get())
            self.tracker.set_budget(amount)
            self.total_budget_var.set("")
            self._refresh_budget_overview()
            messagebox.showinfo("Success", "Total budget updated!")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
            
    def _set_category_budget(self):
        try:
            category = self.budget_category_var.get()
            amount = float(self.category_budget_var.get())
            
            if not category:
                messagebox.showerror("Error", "Please select a category")
                return
                
            self.tracker.set_budget(amount, category)
            self.budget_category_var.set("")
            self.category_budget_var.set("")
            self._refresh_budget_overview()
            messagebox.showinfo("Success", "Category budget updated!")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid amount")
            
    def _refresh_budget_overview(self):
        # Clear current items
        for item in self.budget_tree.get_children():
            self.budget_tree.delete(item)
            
        # Get current month's summary
        summary = self.tracker.get_expense_summary()
        
        # Add total row
        self.budget_tree.insert('', 'end', values=(
            'Total',
            f"${summary['total_budget']:.2f}",
            f"${summary['total_spent']:.2f}",
            f"${summary['budget_remaining'] if summary['budget_remaining'] is not None else 0:.2f}"
        ))
        
        # Add category rows
        for category, data in summary['categories'].items():
            self.budget_tree.insert('', 'end', values=(
                category,
                f"${data['budget']:.2f}",
                f"${data['spent']:.2f}",
                f"${data['remaining'] if data['remaining'] is not None else 0:.2f}"
            ))
            
    def _refresh_charts(self):
        # Clear existing charts
        for widget in self.analysis_tab.winfo_children():
            if isinstance(widget, tk.Canvas):
                widget.destroy()
        
        # Create and display monthly trend chart
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        df = pd.DataFrame(self.tracker.data["expenses"])
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            monthly = df.groupby(df["date"].dt.strftime("%Y-%m"))["amount"].sum()
            monthly.plot(kind="line", marker="o", ax=ax1)
            ax1.set_title("Monthly Spending Trend")
            ax1.set_xlabel("Month")
            ax1.set_ylabel("Amount ($)")
            ax1.grid(True)
            plt.xticks(rotation=45)
            
        canvas1 = FigureCanvasTkAgg(fig1, master=self.analysis_tab)
        canvas1.draw()
        canvas1.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        
        # Create and display category breakdown chart
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        spending = self.tracker.get_spending_by_category()
        if spending:
            plt.pie(spending.values(), labels=spending.keys(), autopct="%1.1f%%")
            ax2.set_title("Spending by Category")
            
        canvas2 = FigureCanvasTkAgg(fig2, master=self.analysis_tab)
        canvas2.draw()
        canvas2.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=1)

def main():
    root = tk.Tk()
    app = ExpenseTrackerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()