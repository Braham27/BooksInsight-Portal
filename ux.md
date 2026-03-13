# User Experience Flow

## 1. User opens the app

User sees a simple screen:

* Chat box
* “Upload tax documents” button
* Progress bar for tax preparation

Example prompt:

> “Hi. I can help organize and estimate your US taxes. Upload your tax documents or answer a few questions to begin.”

---

# 2. User uploads documents

User uploads files like:

* W-2
* 1099-INT
* 1099-DIV
* 1099-NEC
* PDFs or photos

The system:

* scans the documents
* extracts numbers
* identifies document types

User sees:

```
✓ W-2 detected
Employer: Amazon
Wages: $72,400
Federal tax withheld: $9,200
```

User confirms or edits if something is wrong.

---

# 3. AI asks interview questions

The assistant continues like a **TurboTax style interview**, but conversational.

Example:

```
Do you have any dependents?
```

User answers normally:

> “Yes, one child”

AI converts the answer into structured tax data.

More questions:

* filing status
* dependents
* interest income
* additional documents
* deductions

---

# 4. Missing information detection

If something is missing the AI asks.

Example:

```
Your W-2 shows federal withholding.
Do you also have state withholding?
```

or

```
I see interest income reported.
Do you have the 1099-INT document?
```

User uploads or answers.

---

# 5. Tax calculation runs automatically

Once enough information exists:

* The system sends structured data to the **tax engine**.
* The engine calculates tax liability.

The AI **does not do the math**.

User sees a clear breakdown:

```
Total income: $74,200
Standard deduction: $14,600
Taxable income: $59,600
Estimated federal tax: $7,830
Taxes already paid: $9,200

Estimated refund: $1,370
```

---

# 6. Explanation layer

User can ask questions.

Example:

> “Why is my refund $1,370?”

AI explains using the computed values.

Example:

```
Your refund occurs because your employer withheld more tax than your final liability.

Tax owed: $7,830
Withheld: $9,200
Refund: $1,370
```

---

# 7. Error detection

The system checks for inconsistencies.

Example:

```
Warning:
Your W-2 wages appear higher than expected compared to prior entries.

Please confirm:
Wages: $72,400
```

User confirms.

---

# 8. Final tax summary

The user sees a clean dashboard.

```
Tax summary

Income
W-2 wages: $72,400
Interest: $1,800

Deductions
Standard deduction: $14,600

Tax
Tax owed: $7,830
Withheld: $9,200

Refund: $1,370
```

---

# 9. Export results

User can download:

* tax summary
* filled form draft
* accountant-ready package

Example downloads:

```
Download:
✓ Tax summary PDF
✓ Organized tax documents
✓ Draft 1040
```

---

# 10. Human review (optional later)

When you add preparer capability later:

User clicks:

```
Send to tax preparer for review
```

A licensed preparer checks the return.

Then it can be filed.

---

# What the user feels

The experience should feel like:

**ChatGPT + TurboTax + document scanner**

User perception:

* “I just uploaded documents”
* “The AI asked me questions”
* “Everything got organized automatically”
* “I understand my taxes now”

---

# The key advantage

Traditional tax software:

* rigid forms
* confusing UI

Your system:

* natural language
* automatic document reading
* guided conversation

