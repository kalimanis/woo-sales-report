import os
from woocommerce import API
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import tkinter as tk
from tkinter import messagebox

# API credentials
wcapi = API(
    url="",  # Your WooCommerce store URL
    consumer_key="",  # Your WooCommerce consumer key
    consumer_secret="",  # Your WooCommerce consumer secret
    version="wc/v3"  # WooCommerce API version
)

def get_orders():
    page = 1
    while True:
        orders_data = wcapi.get(f"orders?page={page}&per_page=100").json()
        if orders_data:
            for order in orders_data:
                yield order
            page += 1
        else:
            break

def send_sms(monthly_sales):
    url = "https://portal.bulkgate.com/api/1.0/simple/transactional"
    headers = {'Content-Type': 'application/json'}
    current_month = datetime.now().strftime("%m-%Y")
    current_month_sales = monthly_sales.loc[current_month, 'Sales']
    sms_data = {
        "application_id": "",
        "application_token": "",
        "number": "",
        "text": f"hello name, Your sales for this month are: {current_month_sales} euro"
    }
    response = requests.post(url, headers=headers, json=sms_data)
    if response.status_code == 200:
        print("SMS sent successfully.")
    else:
        print("Failed to send SMS.")

def send_email(monthly_sales):
    smtp_host = ''
    smtp_port = ''
    smtp_user = ''
    smtp_pass = ''
    current_month = datetime.now().strftime("%m-%Y")
    current_month_sales = monthly_sales.loc[current_month, 'Sales']
    email_text = f'The sales for {current_month} are: {current_month_sales} euro'
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = ''
    msg['Subject'] = 'Monthly Sales Report'
    msg.attach(MIMEText(email_text))
    with open('sales_graph.png', 'rb') as f:
        img = MIMEImage(f.read())
    img.add_header('Content-Disposition', 'attachment', filename='sales_graph.png')
    msg.attach(img)
    server = smtplib.SMTP(smtp_host, smtp_port)
    server.starttls()
    server.login(smtp_user, smtp_pass)
    server.send_message(msg)
    server.quit()

def create_report():
    orders = list(get_orders())
    if orders:
        data = []
        for order in orders:
            date_created = datetime.strptime(order['date_created'], "%Y-%m-%dT%H:%M:%S")
            year_month = date_created.strftime("%m-%Y")
            data.append([year_month, float(order['total'])])
        df = pd.DataFrame(data, columns=['Year-Month', 'Sales'])
        monthly_sales = df.groupby(['Year-Month']).sum()
        monthly_sales = monthly_sales.sort_index()
        plt.figure(figsize=(10, 6))
        plt.plot(monthly_sales.index, monthly_sales['Sales'], marker='o', linestyle='-', color='b', label='Sales')
        for x, y in zip(monthly_sales.index, monthly_sales['Sales']):
            plt.text(x, y, str(y), ha='center', va='bottom', fontsize=8)
        average_sales = monthly_sales['Sales'].mean()
        plt.axhline(y=average_sales, color='r', linestyle='--', label='Average Sales')
        plt.text(1.02, average_sales, f'Avg: {average_sales:.2f}', va='center', ha="left", bbox=dict(facecolor="w", alpha=0.5),
                 transform=plt.gca().get_yaxis_transform())
        plt.title('Sales per Month')
        plt.xlabel('Month and Year')
        plt.ylabel('Sales')
        plt.legend()
        plt.xticks(rotation=45, fontsize=10)
        plt.gca().xaxis.set_major_locator(plt.MaxNLocator(10))
        plt.grid(True)
        plt.tight_layout()
        plt.savefig('sales_graph.png')
        
        return monthly_sales
    else:
        print("No orders found")

def on_submit():
    monthly_sales = create_report()
    
    email_val = email_var.get()
    sms_val = sms_var.get()
    
    if email_val:
        send_email(monthly_sales)
    if sms_val:
        send_sms(monthly_sales)
    
    if not email_val and not sms_val:
        messagebox.showwarning("Warning", "Please select at least one option!")
    else:
        root.destroy()

root = tk.Tk()
root.title("Report Sending Options")

label = tk.Label(root, text="How would you like to send the report?")
label.pack(pady=20)

email_var = tk.BooleanVar()
sms_var = tk.BooleanVar()

email_cb = tk.Checkbutton(root, text="Email", variable=email_var)
email_cb.pack(pady=5)

sms_cb = tk.Checkbutton(root, text="SMS", variable=sms_var)
sms_cb.pack(pady=5)

submit_button = tk.Button(root, text="Submit", command=on_submit)
submit_button.pack(pady=20)

root.mainloop()
