"""
Expense Splitter & Group Tab Tracker
=====================================
A Python module and interactive CLI for tracking shared group expenses,
calculating net balances, and computing minimal debt settlements.

Repository: https://github.com/tnuislostq/Expense-Splitter-Group-Tab-Tracker
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple


class SplitType(str, Enum):
    EQUAL = "EQUAL"
    EXACT = "EXACT"
    PERCENTAGE = "PERCENTAGE"
    SHARES = "SHARES"


class Expense:
    """Represents a single group expenditure."""

    def __init__(
        self,
        title: str,
        amount: float,
        paid_by: str,
        split_type: SplitType = SplitType.EQUAL,
        splits: Optional[Dict[str, float]] = None,
        category: str = "General",
        date_str: Optional[str] = None,
        expense_id: Optional[str] = None,
    ):
        self.id = expense_id or str(uuid.uuid4())[:8]
        self.title = title
        self.amount = round(float(amount), 2)
        self.paid_by = paid_by
        self.split_type = split_type
        self.category = category
        self.date_str = date_str or datetime.now().strftime("%Y-%m-%d %H:%M")
        self.splits = splits or {}  # Dict[user_name, amount_owed]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "amount": self.amount,
            "paid_by": self.paid_by,
            "split_type": self.split_type.value,
            "category": self.category,
            "date": self.date_str,
            "splits": self.splits,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        return cls(
            title=data["title"],
            amount=data["amount"],
            paid_by=data["paid_by"],
            split_type=SplitType(data["split_type"]),
            splits=data.get("splits", {}),
            category=data.get("category", "General"),
            date_str=data.get("date"),
            expense_id=data.get("id"),
        )


class Settlement:
    """Represents a recorded payment between two group members."""

    def __init__(
        self,
        from_user: str,
        to_user: str,
        amount: float,
        date_str: Optional[str] = None,
        settlement_id: Optional[str] = None,
    ):
        self.id = settlement_id or str(uuid.uuid4())[:8]
        self.from_user = from_user
        self.to_user = to_user
        self.amount = round(float(amount), 2)
        self.date_str = date_str or datetime.now().strftime("%Y-%m-%d %H:%M")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from_user": self.from_user,
            "to_user": self.to_user,
            "amount": self.amount,
            "date": self.date_str,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Settlement":
        return cls(
            from_user=data["from_user"],
            to_user=data["to_user"],
            amount=data["amount"],
            date_str=data.get("date"),
            settlement_id=data.get("id"),
        )


class GroupTabTracker:
    """Manages members, expenses, balances, and debt simplification."""

    def __init__(self, group_name: str = "My Group", currency: str = "₹"):
        self.group_name = group_name
        self.currency = currency
        self.members: List[str] = []
        self.expenses: List[Expense] = []
        self.settlements: List[Settlement] = []

    def add_member(self, name: str) -> bool:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Member name cannot be empty.")
        if clean_name in self.members:
            return False
        self.members.append(clean_name)
        return True

    def remove_member(self, name: str) -> bool:
        if name not in self.members:
            return False
        balances = self.calculate_balances()
        if abs(balances.get(name, 0.0)) > 0.01:
            raise ValueError(f"Cannot remove {name}: active balance is {self.currency}{balances[name]:.2f}.")
        self.members.remove(name)
        return True

    def add_expense(
        self,
        title: str,
        amount: float,
        paid_by: str,
        participants: Optional[List[str]] = None,
        split_type: SplitType = SplitType.EQUAL,
        split_details: Optional[Dict[str, float]] = None,
        category: str = "General",
    ) -> Expense:
        if amount <= 0:
            raise ValueError("Expense amount must be positive.")
        if paid_by not in self.members:
            raise ValueError(f"Payer '{paid_by}' is not in the group.")

        participants = participants or list(self.members)
        for p in participants:
            if p not in self.members:
                raise ValueError(f"Participant '{p}' is not in the group.")

        if not participants:
            raise ValueError("An expense must involve at least one participant.")

        computed_splits: Dict[str, float] = {}

        if split_type == SplitType.EQUAL:
            n = len(participants)
            base_share = round(amount / n, 2)
            computed_splits = {p: base_share for p in participants}
            diff = round(amount - sum(computed_splits.values()), 2)
            if diff != 0:
                computed_splits[participants[0]] = round(computed_splits[participants[0]] + diff, 2)

        elif split_type == SplitType.EXACT:
            if not split_details:
                raise ValueError("Exact amounts must be provided in split_details.")
            total_specified = round(sum(split_details.values()), 2)
            if abs(total_specified - round(amount, 2)) > 0.01:
                raise ValueError(
                    f"Exact splits sum ({total_specified}) does not match total expense ({amount})."
                )
            computed_splits = {p: round(split_details.get(p, 0.0), 2) for p in participants}

        elif split_type == SplitType.PERCENTAGE:
            if not split_details:
                raise ValueError("Percentages must be provided in split_details.")
            total_pct = round(sum(split_details.values()), 2)
            if abs(total_pct - 100.0) > 0.01:
                raise ValueError(f"Percentages must sum to 100. Current sum: {total_pct}%")
            computed_splits = {
                p: round(amount * (split_details.get(p, 0.0) / 100.0), 2)
                for p in participants
            }
            diff = round(amount - sum(computed_splits.values()), 2)
            if diff != 0:
                computed_splits[participants[0]] = round(computed_splits[participants[0]] + diff, 2)

        elif split_type == SplitType.SHARES:
            if not split_details:
                raise ValueError("Shares must be provided in split_details.")
            total_shares = sum(split_details.values())
            if total_shares <= 0:
                raise ValueError("Total shares must be greater than zero.")
            computed_splits = {
                p: round(amount * (split_details.get(p, 0.0) / total_shares), 2)
                for p in participants
            }
            diff = round(amount - sum(computed_splits.values()), 2)
            if diff != 0:
                computed_splits[participants[0]] = round(computed_splits[participants[0]] + diff, 2)

        expense = Expense(
            title=title,
            amount=amount,
            paid_by=paid_by,
            split_type=split_type,
            splits=computed_splits,
            category=category,
        )
        self.expenses.append(expense)
        return expense

    def record_settlement(self, from_user: str, to_user: str, amount: float) -> Settlement:
        if amount <= 0:
            raise ValueError("Settlement amount must be positive.")
        if from_user not in self.members or to_user not in self.members:
            raise ValueError("Both payer and payee must be existing group members.")
        if from_user == to_user:
            raise ValueError("Payer and payee cannot be the same person.")

        settlement = Settlement(from_user=from_user, to_user=to_user, amount=amount)
        self.settlements.append(settlement)
        return settlement

    def calculate_balances(self) -> Dict[str, float]:
        """
        Calculates net balance for each member.
        Positive (> 0): Member is owed money (creditor).
        Negative (< 0): Member owes money (debtor).
        """
        balances: Dict[str, float] = {m: 0.0 for m in self.members}

        for exp in self.expenses:
            balances[exp.paid_by] = balances.get(exp.paid_by, 0.0) + exp.amount
            for debtor, share in exp.splits.items():
                balances[debtor] = balances.get(debtor, 0.0) - share

        for stl in self.settlements:
            balances[stl.from_user] = balances.get(stl.from_user, 0.0) + stl.amount
            balances[stl.to_user] = balances.get(stl.to_user, 0.0) - stl.amount

        return {k: round(v, 2) for k, v in balances.items()}

    def simplify_debts(self) -> List[Tuple[str, str, float]]:
        """
        Calculates minimum transactions needed to settle all debts.
        Returns a list of tuples: (debtor, creditor, amount).
        Uses a greedy balance-matching algorithm.
        """
        balances = self.calculate_balances()
        creditors = []
        debtors = []

        for member, bal in balances.items():
            if bal > 0.01:
                creditors.append([member, bal])
            elif bal < -0.01:
                debtors.append([member, abs(bal)])

        creditors.sort(key=lambda x: x[1], reverse=True)
        debtors.sort(key=lambda x: x[1], reverse=True)

        transactions = []
        c_idx, d_idx = 0, 0

        while c_idx < len(creditors) and d_idx < len(debtors):
            c_member, c_amount = creditors[c_idx]
            d_member, d_amount = debtors[d_idx]

            settle_amount = min(c_amount, d_amount)
            settle_amount = round(settle_amount, 2)

            if settle_amount > 0:
                transactions.append((d_member, c_member, settle_amount))

            creditors[c_idx][1] = round(c_amount - settle_amount, 2)
            debtors[d_idx][1] = round(d_amount - settle_amount, 2)

            if creditors[c_idx][1] <= 0.01:
                c_idx += 1
            if debtors[d_idx][1] <= 0.01:
                d_idx += 1

        return transactions

    def get_summary_stats(self) -> dict:
        total_spent = round(sum(e.amount for e in self.expenses), 2)
        category_spending: Dict[str, float] = {}
        for e in self.expenses:
            category_spending[e.category] = round(
                category_spending.get(e.category, 0.0) + e.amount, 2
            )

        paid_by_member: Dict[str, float] = {m: 0.0 for m in self.members}
        for e in self.expenses:
            paid_by_member[e.paid_by] = round(paid_by_member[e.paid_by] + e.amount, 2)

        return {
            "group_name": self.group_name,
            "total_expenses_count": len(self.expenses),
            "total_spent": total_spent,
            "category_spending": category_spending,
            "paid_by_member": paid_by_member,
        }

    def to_json(self, filepath: str) -> None:
        data = {
            "group_name": self.group_name,
            "currency": self.currency,
            "members": self.members,
            "expenses": [e.to_dict() for e in self.expenses],
            "settlements": [s.to_dict() for s in self.settlements],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def from_json(cls, filepath: str) -> "GroupTabTracker":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        tracker = cls(group_name=data.get("group_name", "My Group"), currency=data.get("currency", "₹"))
        tracker.members = data.get("members", [])
        tracker.expenses = [Expense.from_dict(e) for e in data.get("expenses", [])]
        tracker.settlements = [Settlement.from_dict(s) for s in data.get("settlements", [])]
        return tracker


# -------------------------------------------------------------
# CLI Interface & Demo
# -------------------------------------------------------------
def print_banner(tracker: GroupTabTracker):
    print("=" * 60)
    print(f"   📊 {tracker.group_name.upper()} - EXPENSE SPLITTER & TAB TRACKER")
    print("=" * 60)


def display_balances(tracker: GroupTabTracker):
    print(f"\n--- Current Member Balances ({tracker.currency}) ---")
    balances = tracker.calculate_balances()
    if not balances:
        print("No members found in group.")
        return

    for member, bal in balances.items():
        if bal > 0.01:
            status = f"🟢 is owed {tracker.currency}{bal:.2f}"
        elif bal < -0.01:
            status = f"🔴 owes {tracker.currency}{abs(bal):.2f}"
        else:
            status = "⚪ all settled up (0.00)"
        print(f"  • {member:15s} : {status}")


def display_settlement_plan(tracker: GroupTabTracker):
    print(f"\n--- Suggested Debt Simplification Plan ---")
    plans = tracker.simplify_debts()
    if not plans:
        print("✅ Everyone is settled up! No transactions needed.")
        return

    print(f"Minimal {len(plans)} transaction(s) to settle all group tabs:")
    for idx, (debtor, creditor, amt) in enumerate(plans, 1):
        print(f"  {idx}. {debtor} ➡️  pays {creditor}: {tracker.currency}{amt:.2f}")


def display_analytics(tracker: GroupTabTracker):
    stats = tracker.get_summary_stats()
    print(f"\n--- Group Spending Analytics ---")
    print(f"Total Group Expenditure: {tracker.currency}{stats['total_spent']:.2f}")
    print(f"Total Recorded Expenses: {stats['total_expenses_count']}")

    print("\nSpending by Category:")
    for cat, amt in stats["category_spending"].items():
        pct = (amt / stats["total_spent"] * 100) if stats["total_spent"] > 0 else 0
        print(f"  • {cat:15s} : {tracker.currency}{amt:8.2f} ({pct:5.1f}%)")

    print("\nTotal Contributed by Member:")
    for mem, amt in stats["paid_by_member"].items():
        print(f"  • {mem:15s} : {tracker.currency}{amt:8.2f}")


def run_demo():
    print("\n🚀 Initializing Sample Demo: 'Weekend Goa Trip'...\n")
    tracker = GroupTabTracker(group_name="Goa Weekend Trip", currency="₹")
    for name in ["Aarav", "Tanu", "Rohan", "Sneha"]:
        tracker.add_member(name)

    tracker.add_expense(
        title="Resort Stay (2 Nights)",
        amount=12000.0,
        paid_by="Tanu",
        category="Accommodation",
    )

    tracker.add_expense(
        title="SUV Rental & Fuel",
        amount=6400.0,
        paid_by="Aarav",
        category="Transport",
    )

    tracker.add_expense(
        title="Seafood Dinner",
        amount=3600.0,
        paid_by="Rohan",
        participants=["Tanu", "Rohan", "Sneha"],
        category="Food",
    )

    tracker.add_expense(
        title="Water Sports & Scuba",
        amount=5000.0,
        paid_by="Sneha",
        split_type=SplitType.EXACT,
        participants=["Aarav", "Tanu", "Sneha"],
        split_details={"Aarav": 2000.0, "Tanu": 1500.0, "Sneha": 1500.0},
        category="Activities",
    )

    print_banner(tracker)
    display_balances(tracker)
    display_settlement_plan(tracker)
    display_analytics(tracker)

    print("\n✨ Recording a partial settlement: Sneha pays Tanu ₹1,000...")
    tracker.record_settlement(from_user="Sneha", to_user="Tanu", amount=1000.0)
    display_balances(tracker)
    display_settlement_plan(tracker)
    return tracker


def main():
    tracker = GroupTabTracker(group_name="My Friends Group", currency="₹")
    tracker.members = ["Tanu", "Priya", "Rahul"]

    while True:
        print_banner(tracker)
        print("1. View Balances")
        print("2. Add an Expense")
        print("3. View Debt Simplification Plan")
        print("4. Record a Settlement / Payment")
        print("5. Spending Analytics & History")
        print("6. Manage Members (Add / Remove)")
        print("7. Export / Import Data (JSON)")
        print("8. Run Sample Demo Trip")
        print("0. Exit")
        choice = input("\nEnter choice [0-8]: ").strip()

        if choice == "1":
            display_balances(tracker)
        elif choice == "2":
            try:
                title = input("Expense description: ").strip()
                amount = float(input(f"Total amount ({tracker.currency}): ").strip())
                print(f"Available members: {', '.join(tracker.members)}")
                paid_by = input("Paid by: ").strip()
                cat = input("Category (e.g. Food, Travel, Stay) [General]: ").strip() or "General"

                print("\nSelect Split Type:")
                print("1. Equal split among all members")
                print("2. Equal split among specific members")
                print("3. Exact amounts")
                print("4. Percentage split")
                stype_choice = input("Choice [1-4]: ").strip()

                if stype_choice == "1":
                    tracker.add_expense(title, amount, paid_by, category=cat)
                elif stype_choice == "2":
                    sel = input("Enter member names (comma-separated): ").split(",")
                    parts = [s.strip() for s in sel if s.strip()]
                    tracker.add_expense(title, amount, paid_by, participants=parts, category=cat)
                elif stype_choice == "3":
                    splits = {}
                    for m in tracker.members:
                        val = float(input(f"  Exact share for {m} ({tracker.currency}): ") or 0)
                        splits[m] = val
                    tracker.add_expense(
                        title, amount, paid_by, split_type=SplitType.EXACT, split_details=splits, category=cat
                    )
                elif stype_choice == "4":
                    splits = {}
                    for m in tracker.members:
                        val = float(input(f"  Percentage for {m} (%): ") or 0)
                        splits[m] = val
                    tracker.add_expense(
                        title, amount, paid_by, split_type=SplitType.PERCENTAGE, split_details=splits, category=cat
                    )
                print("✅ Expense added successfully!")
            except Exception as e:
                print(f"❌ Error adding expense: {e}")

        elif choice == "3":
            display_settlement_plan(tracker)
        elif choice == "4":
            try:
                print(f"Members: {', '.join(tracker.members)}")
                from_u = input("Who paid? (Debtor): ").strip()
                to_u = input("To whom? (Creditor): ").strip()
                amt = float(input(f"Amount ({tracker.currency}): ").strip())
                tracker.record_settlement(from_u, to_u, amt)
                print("✅ Settlement recorded!")
            except Exception as e:
                print(f"❌ Error recording settlement: {e}")
        elif choice == "5":
            display_analytics(tracker)
        elif choice == "6":
            print(f"Current members: {', '.join(tracker.members)}")
            action = input("Type 'add' or 'remove': ").strip().lower()
            m_name = input("Member name: ").strip()
            if action == "add":
                if tracker.add_member(m_name):
                    print(f"✅ Added {m_name}")
                else:
                    print(f"Member already exists.")
            elif action == "remove":
                try:
                    if tracker.remove_member(m_name):
                        print(f"✅ Removed {m_name}")
                except Exception as e:
                    print(f"❌ {e}")
        elif choice == "7":
            sub = input("Type 'save' to export or 'load' to import: ").strip().lower()
            fname = input("Filename [group_tab.json]: ").strip() or "group_tab.json"
            if sub == "save":
                tracker.to_json(fname)
                print(f"✅ Saved to {fname}")
            elif sub == "load":
                try:
                    tracker = GroupTabTracker.from_json(fname)
                    print(f"✅ Loaded from {fname}")
                except Exception as e:
                    print(f"❌ Failed to load: {e}")
        elif choice == "8":
            tracker = run_demo()
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        run_demo()
    else:
        main()
