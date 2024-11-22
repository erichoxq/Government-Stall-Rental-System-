import sqlite3
import tkinter.messagebox as messagebox
import customtkinter as ctk
from tkinter import ttk, Radiobutton, Tk, StringVar, Toplevel, Frame, Label, Entry, Button, Text, Scrollbar, filedialog, \
    END, IntVar, Canvas, DISABLED, NORMAL, Listbox, OptionMenu, VERTICAL, BooleanVar, Checkbutton
from tkinter.ttk import Combobox
import datetime
from PIL import Image, ImageTk, ImageOps, ImageDraw, ImageSequence
from tkinter.ttk import Progressbar, Style
import cv2
import numpy as np
import face_recognition
import os
import pyperclip
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from fpdf import FPDF
import re
import random
from dateutil.relativedelta import relativedelta
from tkcalendar import DateEntry
import math
from flask import Flask, request, jsonify, render_template
import phonenumbers
from phonenumbers import geocoder, carrier
import webbrowser
import threading
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkintermapview import TkinterMapView
import time
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
import tempfile

app = Flask(__name__)

root = Tk()

# Constants
WIDTH = 800
HEIGHT = 700

# Create variables
USERNAME_LOGIN = StringVar()
PASSWORD_LOGIN = StringVar()
USERNAME_REGISTER = StringVar()
PASSWORD_REGISTER = StringVar()
FULLNAME = StringVar()
IC = StringVar()
DATE_OF_BIRTH = StringVar()
EMAIL_ADDRESS = StringVar()
PHONE_NUMBER = StringVar()

conn = sqlite3.connect("stall_rental_system.db")  # connection to database
cursor = conn.cursor()  # use to execute the sql queries and fetch results from db

# Global variables to store the logged-in user's information
logged_in_user = {}

# Global variable to store the generated verification code
verification_code = ""

# Store user location data in memory (for simplicity, use a database in production)
locations = {}


# Database
def Database():
    global conn, cursor
    conn = sqlite3.connect("stall_rental_system.db")
    cursor = conn.cursor()

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `tenant` (tenant_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT(20), "
        "password TEXT(20), fullname TEXT(20), ic TEXT(20), date_of_birth DATE, email_address TEXT(30), phone_number TEXT(20), face_id_image TEXT(30), face_embedding TEXT(30))")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `admin`(admin_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT(20), "
        "password TEXT(20), fullname TEXT(20), ic TEXT(20), date_of_birth DATE, email_address TEXT(30), phone_number TEXT(20), face_id_image TEXT(30), face_embedding TEXT(30))")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `stall` (stall_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, "
        "location TEXT NOT NULL, size TEXT(20), rent_price_per_month REAL NOT NULL, latitude REAL NOT NULL, longitude REAL NOT NULL, stall_image TEXT NOT NULL,admin_id INTEGER NOT NULL,FOREIGN KEY (admin_id) REFERENCES admins(admin_id))")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `rental` (rental_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, tenant_id INTEGER NOT NULL, stall_id INTEGER NOT NULL, start_date DATE NOT NULL, end_date DATE NOT NULL, "
        "FOREIGN KEY (tenant_id) REFERENCES tenant(tenant_id), FOREIGN KEY (stall_id) REFERENCES stall(stall_id))")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `payment` (payment_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, tenant_id INTEGER NOT NULL,"
        "rental_id INTEGER NOT NULL, paid_periods TEXT NOT NULL, payment_date DATE , amount REAL , "
        "payment_status TEXT NOT NULL,payment_type TEXT, FOREIGN KEY (tenant_id) REFERENCES tenant(tenant_id), FOREIGN KEY (rental_id) REFERENCES rental(rental_id))")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `feedback` (feedback_id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id INTEGER, admin_id INTEGER, feedback TEXT NOT NULL, response TEXT, feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "response_date TIMESTAMP, FOREIGN KEY(tenant_id) REFERENCES tenant(tenant_id), FOREIGN KEY(admin_id) REFERENCES admin(admin_id))")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `attendance_records` (attendance_records_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, tenant_id INTEGER NOT NULL, stall_id INTEGER NOT NULL, "
        "latitude REAL NOT NULL, longitude REAL NOT NULL, attendance_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, attendance_count INTEGER DEFAULT 0, attendance_status TEXT,scan_status TEXT, FOREIGN KEY (tenant_id) REFERENCES tenant(tenant_id), FOREIGN KEY (stall_id) REFERENCES stall(stall_id))")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `notification` (notification_id INTEGER PRIMARY KEY AUTOINCREMENT, recipient TEXT NOT NULL CHECK (recipient IN ('tenant', 'admin', 'auditor')), recipient_id INTEGER NOT NULL, "
        "message TEXT NOT NULL, notification_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, is_read BOOLEAN DEFAULT 0, FOREIGN KEY (recipient_id) REFERENCES tenant(tenant_id) ON DELETE CASCADE, FOREIGN KEY (recipient_id) REFERENCES admin(admin_id) ON DELETE CASCADE, FOREIGN KEY (recipient_id) REFERENCES auditor(auditor_id) ON DELETE CASCADE)")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `applications` (application_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, tenant_id INTEGER NOT NULL, stall_id INTEGER NOT NULL, reason TEXT NOT NULL, start_date DATE NOT NULL,"
        "duration INTEGER NOT NULL, status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')), application_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, "
        "FOREIGN KEY (tenant_id) REFERENCES tenant(tenant_id), FOREIGN KEY (stall_id) REFERENCES stall(stall_id))")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `auditor` (auditor_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT(20), password TEXT(20), fullname TEXT(20), ic TEXT(20), "
        "date_of_birth DATE, email_address TEXT(30), phone_number TEXT(20),face_id_image TEXT(30), face_embedding TEXT(30))")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `auditor_assignments` (assignment_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, auditor_id INTEGER NOT NULL, tenant_id INTEGER NOT NULL, attendance_records_id INTEGER NOT NULL, assignment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,"
        "FOREIGN KEY (auditor_id) REFERENCES auditor(auditor_id),FOREIGN KEY (tenant_id) REFERENCES tenant(tenant_id),FOREIGN KEY (attendance_records_id) REFERENCES attendance_records(attendance_records_id))")

    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `evidence` (evidence_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, assignment_id INTEGER NOT NULL, image_path TEXT NOT NULL, reason TEXT NOT NULL, "
        "upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, status TEXT CHECK (status IN ('pending', 'approve', 'reject')) DEFAULT 'pending', FOREIGN KEY (assignment_id) REFERENCES auditor_assignments(assignment_id))")

    conn.commit()





# Class
class Tenant:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def get_tenant_by_username(self, username):
        """Fetch a tenant by username."""
        self.cursor.execute("SELECT username FROM tenant WHERE username = ?", (username,))
        return self.cursor.fetchone()

    def register_tenant(self, username, password, fullname, ic, dob, email, phone_number):
        """Insert or update a tenant in the tenant table based on IC."""
        existing_tenant = self.get_tenant_by_ic(ic)
        if existing_tenant:
            # Update existing tenant
            self.cursor.execute(
                "UPDATE tenant SET username = ?, password = ?, fullname = ?, date_of_birth = ?, email_address = ?, phone_number = ? WHERE ic = ?",
                (username, password, fullname, dob, email, phone_number, ic)
            )
        else:
            # Insert new tenant
            self.cursor.execute(
                "INSERT INTO tenant (username, password, fullname, ic, date_of_birth, email_address, phone_number) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, password, fullname, ic, dob, email, phone_number)
            )
        self.conn.commit()

    def get_tenant_by_credentials(self, username, password):
        """Fetch a tenant by username and password."""
        self.cursor.execute("SELECT * FROM `tenant` WHERE `username` = ? AND `password` = ?", (username, password))
        return self.cursor.fetchone()

    def get_tenant_by_ic(self, ic):
        """Retrieve tenant data by IC."""
        self.cursor.execute("SELECT * FROM tenant WHERE ic = ?", (ic,))
        return self.cursor.fetchone()

class Admin:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def get_admin_by_username(self, username):
        """Fetch an admin by username."""
        self.cursor.execute("SELECT username FROM admin WHERE username = ?", (username,))
        return self.cursor.fetchone()

    def register_admin(self, username, password, fullname, ic, dob, email, phone_number):
        """Insert a new admin into the admin table."""
        self.cursor.execute(
            "INSERT INTO admin (username, password, fullname, ic, date_of_birth, email_address, phone_number) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username, password, fullname, ic, dob, email, phone_number)
        )
        self.conn.commit()

    def get_admin_by_credentials(self, username, password):
        """Fetch an admin by username and password."""
        self.cursor.execute("SELECT * FROM `admin` WHERE `username` = ? AND `password` = ?", (username, password))
        return self.cursor.fetchone()

    def get_admin_by_ic(self, ic):
        """Retrieve admin data by IC."""
        self.cursor.execute("SELECT * FROM admin WHERE ic = ?", (ic,))
        return self.cursor.fetchone()

class Auditor:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def get_auditor_by_username(self, username):
        """Fetch an auditor by username."""
        self.cursor.execute("SELECT username FROM auditor WHERE username = ?", (username,))
        return self.cursor.fetchone()

    def register_or_update_auditor(self, username, password, fullname, ic, dob, email, phone_number):
        """Update an existing auditor's information based on IC, or register a new one if not found."""
        existing_auditor = self.get_auditor_by_ic(ic)

        if existing_auditor:
            # Update the auditor details based on IC
            self.cursor.execute(
                """
                UPDATE auditor 
                SET username = ?, password = ?, fullname = ?, date_of_birth = ?, email_address = ?, phone_number = ?
                WHERE ic = ?
                """,
                (username, password, fullname, dob, email, phone_number, ic)
            )
        else:
            # Optionally, insert a new auditor if not found (or handle it differently if needed)
            self.cursor.execute(
                "INSERT INTO auditor (username, password, fullname, ic, date_of_birth, email_address, phone_number) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (username, password, fullname, ic, dob, email, phone_number)
            )

        self.conn.commit()

    def get_auditor_by_credentials(self, username, password):
        """Fetch an admin by username and password."""
        self.cursor.execute("SELECT * FROM `auditor` WHERE `username` = ? AND `password` = ?", (username, password))
        return self.cursor.fetchone()

    def get_auditor_by_ic(self, ic):
        """Retrieve auditor data by IC."""
        self.cursor.execute("SELECT * FROM auditor WHERE ic = ?", (ic,))
        return self.cursor.fetchone()

class Stall:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def add_stall(self, location, size, rent_price_per_month, latitude, longitude, image_path, admin_id):
        try:
            # Insert a new stall into the database
            self.cursor.execute("""
                INSERT INTO stall (location, size, rent_price_per_month, latitude, longitude, stall_image, admin_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (location, size, rent_price_per_month, latitude, longitude, image_path, admin_id))

            self.conn.commit()  # Commit the changes to the database
            messagebox.showinfo("Success", "Stall added successfully.")

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to add stall: {e}")

    def update_stall(self, stall_id, new_location, new_size, new_rent_price_per_month, new_latitude, new_longitude, new_image_path):
        try:
            # Update the stall information in the database
            self.cursor.execute("""
                UPDATE stall
                SET location = ?, size = ?, rent_price_per_month = ?, latitude = ?, longitude = ?, stall_image = ?
                WHERE stall_id = ?
            """, (
            new_location, new_size, new_rent_price_per_month, new_latitude, new_longitude, new_image_path, stall_id))

            self.conn.commit()  # Commit the changes to the database
            messagebox.showinfo("Success", "Stall updated successfully.")

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to update stall: {e}")

    def delete_stall(self, stall_id):
        self.cursor.execute("DELETE FROM stall WHERE stall_id = ?", (stall_id,))
        self.conn.commit()

class Applications:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def insert_application(self, logged_in_user, stall_id, reason, duration, start_date, application_date):
        self.cursor.execute(
            "INSERT INTO applications (tenant_id, stall_id, reason, duration, start_date, status, application_date) "
            "VALUES ((SELECT tenant_id FROM tenant WHERE username = ?), ?, ?, ?, ?, 'pending', ?)",
            (logged_in_user['username'], stall_id, reason, int(duration), start_date, application_date)
        )
        self.conn.commit()

    def approve_application(self, application_id):
        self.cursor.execute(
            "UPDATE applications SET status = 'approved' WHERE application_id = ?",
            (application_id,)
        )
        self.conn.commit()

    def reject_application(self, application_id):
        self.cursor.execute(
            "UPDATE applications SET status = 'rejected' WHERE application_id = ?",
            (application_id,)
        )
        self.conn.commit()

class Auditor_assignments:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def insert_assignment(self, auditor_id, tenant_id, attendance_record_id):
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Insert assignment record into the database
        self.cursor.execute(
            """
            INSERT INTO auditor_assignments (auditor_id, tenant_id, attendance_records_id, assignment_date)
            VALUES (?, ?, ?, ?)
            """,
            (auditor_id, tenant_id, attendance_record_id, current_time)
        )
        self.conn.commit()

class Evidence:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def upload_evidence(self, assignment_id, file_path, reason, upload_date, status='pending'):
        """Insert evidence into the database."""
        try:
            self.cursor.execute(
                """INSERT INTO evidence (assignment_id, image_path, reason, upload_date, status) 
                   VALUES (?, ?, ?, ?, ?)""",
                (assignment_id, file_path, reason, upload_date, status)
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error uploading evidence: {str(e)}")
            return False


class Rental:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def insert_rental(self, tenant_id, stall_id, start_date, end_date=None):
        self.cursor.execute("""
            INSERT INTO rental (tenant_id, stall_id, start_date, end_date) 
            VALUES (?, ?, ?, ?)
        """, (tenant_id, stall_id, start_date, end_date))
        self.conn.commit()

    def delete_rental(self, rental_id):
        self.cursor.execute("DELETE FROM rental WHERE rental_id = ?", (rental_id,))
        self.conn.commit()

class Payment:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def get_unpaid_periods(self, tenant_id):
        # Query to get unpaid periods for a given tenant
        self.cursor.execute(""" 
            SELECT paid_periods 
            FROM payment 
            WHERE tenant_id = ? AND payment_status = 'unpaid' 
        """, (tenant_id,))
        # Fetch the result and return
        unpaid_periods = self.cursor.fetchall()
        return unpaid_periods

    def update_payment(self, tenant_id, rental_id, period, rent_price, payment_type, current_time):
        """Proceed with the payment and mark the period as 'Paid'."""
        # Execute the update to mark the payment as 'paid'
        self.cursor.execute(""" 
            UPDATE payment
            SET payment_date = ?, amount = ?, payment_status = 'paid', payment_type = ?
            WHERE tenant_id = ? AND rental_id = ? AND paid_periods = ? 
        """, (current_time, rent_price, payment_type, tenant_id, rental_id, period))

        # Commit the changes to the database
        self.conn.commit()

class Notification:
    def __init__(self, conn, cursor):
        self.conn = conn
        self.cursor = cursor

    def insert_notification(self, recipient_type, recipient_id, message, current_time):
        # Insert the notification into the database
        self.cursor.execute("""
            INSERT INTO notification (recipient, recipient_id, message, notification_date)
            VALUES (?, ?, ?, ?)
        """, (recipient_type, recipient_id, message, current_time))
        self.conn.commit()

    def notification_exists(self, tenant_id, message, today):
        # Check if the notification already exists for the given tenant and message on today's date
        self.cursor.execute("""
            SELECT COUNT(*) FROM notification
            WHERE recipient_id = ? AND message = ? AND DATE(notification_date) = ?
        """, (tenant_id, message, today))

        return self.cursor.fetchone()[0] > 0




# Register adapter and converter for SQLite to handle datetime.date
def adapt_date(date_obj):
    return date_obj.strftime("%Y-%m-%d")  # Convert date to string

def convert_date(date_str):
    return datetime.datetime.strptime(date_str.decode("utf-8"), "%Y-%m-%d").date()

# Register the adapters
sqlite3.register_adapter(datetime.date, adapt_date)
sqlite3.register_converter("DATE", convert_date)


# send email for check expired rentals
def send_email(recipient_email, subject, body):
    """
    Sends an email to the specified recipient with the given subject and body.
    """
    sender_email = "projectall2.2024@gmail.com"  # Your Gmail address
    sender_password = "xiim atxo oajc mtly"  # App-specific password

    try:
        # Set up the server
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Gmail SMTP server and port
        server.starttls()  # Upgrade to secure connection

        # Log in to the server using the app-specific password
        server.login(sender_email, sender_password)

        # Create the email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send the email
        server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"Email sent to {recipient_email}")

    except smtplib.SMTPAuthenticationError:
        print("Authentication failed. Please check your email credentials.")

    except Exception as e:
        print(f"Failed to send email to {recipient_email}: {e}")

    finally:
        # Disconnect from the server
        server.quit()

def check_expired_rentals():
    """
    Checks for tenants whose rental period has expired and unassigns their stalls.
    """
    try:
        # Get the current date
        current_date = datetime.date.today()
        print(f"Current date: {current_date}")  # Debugging: print the current date

        # Query for rentals where the end_date has passed
        cursor.execute("""
            SELECT tenant_id, stall_id FROM rental WHERE DATE(end_date) < ?
        """, (current_date,))

        expired_rentals = cursor.fetchall()

        if expired_rentals:
            for tenant_id, stall_id in expired_rentals:
                # Notify the tenant and admin by email
                notify_tenant_by_email(tenant_id, stall_id)
                notify_admin_by_email(tenant_id, stall_id)

            # Commit changes to the database
            conn.commit()
            print("Expired rentals processed. Stalls unassigned and notifications sent.")
        else:
            print("No expired rentals found.")

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error checking expired rentals: {e}")

def notify_tenant_by_email(tenant_id, stall_id):
    """
    Sends an email notification to the tenant about their expired rental and logs it in the database.
    """
    cursor.execute("SELECT email_address FROM tenant WHERE tenant_id = ?", (tenant_id,))
    tenant = cursor.fetchone()

    if tenant:
        tenant_email = tenant[0]
        subject = "Rental Expired Notification"
        body = f"Dear Tenant,\n\nYour rental for Stall ID {stall_id} has expired. Please contact the admin for further details.\n\n\nBest regards,\nGovernment Stall Rental System"
        send_email(tenant_email, subject, body)

        # Get the current time
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Log the notification in the database
        cursor.execute("""
            INSERT INTO notification (recipient, recipient_id, message,notification_date) 
            VALUES (?, ?, ?, ?)
        """, ("tenant", tenant_id, body, current_time))
        conn.commit()
    else:
        print(f"Tenant with ID {tenant_id} not found.")

def notify_admin_by_email(tenant_id, stall_id):
    """
    Sends an email notification to a single email address for all admins and logs the notification in the database for each admin.
    """
    # Define the single email for all admins
    single_admin_email = "projectall2.2024@gmail.com"  # Replace with the actual admin email

    # Fetch all admin IDs (we only need the IDs for logging the notifications)
    cursor.execute("SELECT admin_id FROM admin")
    admins = cursor.fetchall()

    if admins:
        subject = "Expired Rental Notification"
        body = f"Dear Admin,\n\nTenant ID {tenant_id} rental for Stall ID {stall_id} has expired."

        # Send email to the single email address
        send_email(single_admin_email, subject, body)

        # Get the current time
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Log the notification for each admin in the database
        for admin_id, in admins:
            cursor.execute("""
                INSERT INTO notification (recipient, recipient_id, message, notification_date) 
                VALUES (?, ?, ?, ?)
            """, ("admin", admin_id, body, current_time))

        # Commit all changes
        conn.commit()
    else:
        print("No admins found.")

def schedule_rental_check():
    """
    Schedules the check_expired_rentals function to run periodically.
    This ensures that the system regularly checks for expired rentals.
    """
    # Call the check_expired_rentals function to check for expired rentals
    check_expired_rentals()

    # Schedule the function to run again after 1 hour (3600000 milliseconds)
    root.after(3600000, schedule_rental_check)



# send verification email
def send_verification_email(email_address):
    global verification_code
    verification_code = str(random.randint(100000, 999999))  # Generate a random 6-digit code

    # Set up the email content
    sender_email = "projectall2.2024@gmail.com"  # Replace with your email
    sender_password = "xiim atxo oajc mtly"  # Replace with your password
    receiver_email = email_address.get()  # User's email address

    subject = "Email Verification Code"
    body = f"Your verification code is {verification_code}"

    # Create the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        # Set up the SMTP server and send the email
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Gmail's SMTP server
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        messagebox.showinfo("Email Sent", "Verification code sent to your email.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send verification email: {e}")

def verify_code_input():
    if entered_code.get() == verification_code:
        Register()  # Call the registration function if the code is correct
        entered_code.set("")  # Clear the verification code entry after registration
    else:
        messagebox.showerror("Error", "Incorrect verification code!")

def verify_code_input_admin():
    if entered_code.get() == verification_code:
        AdminRegister()  # Call the registration function if the code is correct
        entered_code.set("")  # Clear the verification code entry after registration
    else:
        messagebox.showerror("Error", "Incorrect verification code!")

def verify_code_input_auditor():
    if entered_code.get() == verification_code:
        register_auditor()  # Call the registration function if the code is correct
        entered_code.set("")  # Clear the verification code entry after registration
    else:
        messagebox.showerror("Error", "Incorrect verification code!")


# send notification and email for tenant who no make the payment on that period
def notification_exists(recipient_type, recipient_id, message_keyword):
    conn = sqlite3.connect("stall_rental_system.db")
    cursor = conn.cursor()

    # Check if a notification with the specific keyword exists for today
    today = datetime.date.today().strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT COUNT(*) FROM notification 
        WHERE recipient = ? AND recipient_id = ? AND message LIKE ? AND DATE(notification_date) = ?
    """, (recipient_type, recipient_id, f"%{message_keyword}%", today))

    result = cursor.fetchone()[0]
    conn.close()
    return result > 0  # Returns True if a notification exists, False otherwise

def check_overdue_payments():
    conn = sqlite3.connect("stall_rental_system.db")
    cursor = conn.cursor()
    seven_days_ago = datetime.date.today() - datetime.timedelta(days=7)

    # Query for overdue payments
    cursor.execute("""
        SELECT payment_id, tenant_id, paid_periods 
        FROM payment 
        WHERE payment_status = 'unpaid'
    """)
    overdue_payments = cursor.fetchall()

    if overdue_payments:
        print("Checking for overdue payments...")
        overdue_to_notify = []  # List to collect all overdue payments that need notification

        for payment_id, tenant_id, paid_periods in overdue_payments:
            period_start_date = datetime.datetime.strptime(paid_periods.split(" to ")[0], "%d-%m-%Y").date()

            if period_start_date <= seven_days_ago:
                # Tenant notification handling
                message_keyword = f"Dear Tenant,\n\nThis is a reminder that your payment for the period {paid_periods} is overdue. Please make the payment as soon as possible.\n\n\nBest regards,\nGovernment Stall Rental System"

                if not notification_exists("tenant", tenant_id, message_keyword):
                    print(f"Overdue payment found for Tenant ID {tenant_id} for period {paid_periods}")
                    send_notification(tenant_id, payment_id, paid_periods)
                    send_email_to_tenant(tenant_id, paid_periods)
                    overdue_to_notify.append((payment_id, tenant_id, paid_periods))
                else:
                    print(f"Notification and email already sent for Tenant ID {tenant_id} for period {paid_periods}")

        # Send one consolidated email to admin if there are any new overdue payments
        if overdue_to_notify:
            # Get all admin IDs to send notifications in the system
            cursor.execute("SELECT admin_id FROM admin")
            admin_ids = cursor.fetchall()

            # Send individual notifications to each admin in the system
            for (admin_id,) in admin_ids:
                for payment_id, tenant_id, paid_periods in overdue_to_notify:
                    admin_message_keyword = f"Dear Admin,\n\nOverdue payment:\nTenant ID: {tenant_id}, Period: {paid_periods}, Payment ID: {payment_id}\nPlease take appropriate action.\n\n\nBest regards,\nGovernment Stall Rental System"

                    if not notification_exists("admin", admin_id, admin_message_keyword):
                        print(f"Sending overdue payment notification for Tenant ID {tenant_id} to Admin ID {admin_id}")
                        send_admin_notification(admin_id, payment_id, tenant_id, paid_periods)

            # Send only one email to the admin email address with all overdue payments
            send_email_to_admins(overdue_to_notify)

    conn.close()
    print("Overdue payment check complete.")

def send_email_to_admins(overdue_payments):
    # Single admin email address
    admin_email = "projectall2.2024@gmail.com"

    # Email credentials
    sender_email = "projectall2.2024@gmail.com"
    sender_password = "xiim atxo oajc mtly"
    subject = "Overdue Payments Alert"

    # Create consolidated email body
    body = "Dear Admin,\n\nOverdue payment:\n"
    for payment_id, tenant_id, paid_periods in overdue_payments:
        body += f" -Tenant ID: {tenant_id}\n  -Period: {paid_periods}\n  -Payment ID: {payment_id}\n\n"
    body += "\nPlease take appropriate action.\n\n\nBest regards,\nGovernment Stall Rental System"

    # Set up the email message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = admin_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, admin_email, msg.as_string())
            print("Overdue payments email sent to admin successfully")
    except Exception as e:
        print(f"Error sending email to admin: {str(e)}")

def send_admin_notification(admin_id, payment_id, tenant_id, paid_periods):
    conn = sqlite3.connect("stall_rental_system.db")
    cursor = conn.cursor()
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Prepare the notification message with unique content
    message = f"Dear Admin,\n\nOverdue payment:\nTenant ID: {tenant_id}, Period: {paid_periods}, Payment ID: {payment_id}\nPlease take appropriate action.\n\n\nBest regards,\nGovernment Stall Rental System"

    # Insert notification for admin
    cursor.execute("""
        INSERT INTO notification (recipient, recipient_id, message, notification_date) 
        VALUES ('admin', ?, ?, ?)
    """, (admin_id, message, current_time))

    conn.commit()
    conn.close()

def send_notification(tenant_id, payment_id, paid_periods):
    conn = sqlite3.connect("stall_rental_system.db")
    cursor = conn.cursor()
    # Get the current time
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # Insert notification into database
    message = f"Dear Tenant,\n\nThis is a reminder that your payment for the period {paid_periods} is overdue. Please make the payment as soon as possible.\n\n\nBest regards,\nGovernment Stall Rental System"
    cursor.execute("""
        INSERT INTO notification (recipient, recipient_id, message, notification_date) 
        VALUES ('tenant', ?, ?, ?)
    """, (tenant_id, message, current_time))

    conn.commit()
    conn.close()

def send_email_to_tenant(tenant_id, paid_periods):
    conn = sqlite3.connect("stall_rental_system.db")
    cursor = conn.cursor()

    # Get tenant's email
    cursor.execute("SELECT email_address FROM tenant WHERE tenant_id = ?", (tenant_id,))
    tenant_email = cursor.fetchone()[0]
    conn.close()

    # Email setup
    sender_email = "projectall2.2024@gmail.com"
    sender_password = "xiim atxo oajc mtly"
    subject = "Payment Overdue Notification"
    body = f"Dear Tenant,\n\nThis is a reminder that your payment for the period {paid_periods} is overdue. Please make the payment as soon as possible.\n\n\nBest regards,\nGovernment Stall Rental System"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = tenant_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Send email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, tenant_email, msg.as_string())





# Auditor
def get_auditor_id_from_username(username):
    # Retrieve auditor ID function
    cursor.execute("SELECT auditor_id FROM auditor WHERE username = ?", (username,))
    result = cursor.fetchone()
    return result[0] if result else None

def open_upload_window(assignment_id, tenant_id, attendance_record_id):
    # Create a new window for uploading evidence
    upload_win = Toplevel()
    upload_win.title("Upload Evidence")
    upload_win.geometry("1920x1080+0+0")
    upload_win.configure(bg="gray")
    upload_win.state("zoomed")

    # Variables to store file path and reason
    selected_image_path = {"path": None}

    def select_image():
        """Open file dialog to select an image and display a preview."""
        file_path = filedialog.askopenfilename(
            title="Select Evidence Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")]
        )

        if file_path:
            selected_image_path["path"] = file_path
            try:
                img = Image.open(file_path)
                img = img.resize((300, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)

                # Display the image preview
                image_label.config(image=photo)
                image_label.image = photo  # Keep reference to avoid garbage collection
            except Exception as e:
                messagebox.showerror("Error", f"Could not open image: {str(e)}")
        else:
            messagebox.showwarning("No Image Selected", "Please select an image.")

    def submit_evidence():
        """Submit the selected image and reason to the database."""
        file_path = selected_image_path["path"]
        reason = reason_text.get("1.0", "end").strip()

        if not file_path:
            messagebox.showwarning("Missing Image", "Please select an image.")
            return

        if not reason:
            messagebox.showwarning("Missing Reason", "Please provide a reason.")
            return

        upload_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # Create an Evidence object and upload the evidence
        evidence = Evidence(conn, cursor)
        success = evidence.upload_evidence(assignment_id, file_path, reason, upload_date)

        if success:
            messagebox.showinfo("Success", "Evidence uploaded successfully.")
            upload_win.destroy()  # Close the upload window
            view_auditor_assignments()
        else:
            messagebox.showerror("Error", "Failed to upload evidence.")

    def back():
        """Close the upload window when 'Back' is clicked."""
        upload_win.destroy()
        view_auditor_assignments()

    title_frame = ctk.CTkFrame(upload_win, fg_color="white", corner_radius=10)
    title_frame.pack(side="top", fill="x", padx=10, pady=10)

    title_label = Label(title_frame, text="Upload Evidence:", font=('Bauhaus 93', 24), bg="white",
                        fg='#0016BA', bd=18)
    title_label.pack(side='top', pady=10)

    # Fetch tenant information
    cursor.execute(
        "SELECT fullname, ic, date_of_birth, email_address, phone_number FROM tenant WHERE tenant_id = ?",
        (tenant_id,))
    tenant_info = cursor.fetchone()

    # Fetch attendance record information
    cursor.execute(
        """
        SELECT attendance_time, attendance_count, attendance_status, scan_status
        FROM attendance_records 
        WHERE attendance_records_id = ?
        """, (attendance_record_id,))
    attendance_record = cursor.fetchone()

    # Display tenant info and attendance record at the top
    left_frame = ctk.CTkFrame(upload_win, fg_color="white", corner_radius=10)
    left_frame.pack(side="left", expand=True, fill="both", padx=10, pady=10)

    tenant_frame = ctk.CTkFrame(left_frame, fg_color="#C0C0C0", corner_radius=10)
    tenant_frame.pack(fill="both", expand=True, padx=10, pady=10)

    if tenant_info:
        tenant_label = ctk.CTkLabel(tenant_frame, text="Tenant Information", font=('Helvetica', 16, 'bold'),
                                    text_color="#000080")
        tenant_label.pack(pady=5)
        for title, info in zip(["Full Name: ", "IC: ", "Date of Birth: ", "Email: ", "Phone Number: "], tenant_info):
            info_row = ctk.CTkFrame(tenant_frame, fg_color="#C0C0C0")
            info_row.pack(fill="x", padx=10, pady=2)

            title_label = ctk.CTkLabel(info_row, text=title, font=('Helvetica', 12, 'bold'), text_color="#404040")
            title_label.pack(side="left", padx=5)

            info_label = ctk.CTkLabel(info_row, text=info, font=('Helvetica', 12), text_color="blue")
            info_label.pack(side="left", padx=5)

    attendance_frame = ctk.CTkFrame(left_frame, fg_color="#C0C0C0", corner_radius=10)
    attendance_frame.pack(fill="both", expand=True, padx=10, pady=10)

    if attendance_record:
        attendance_label = ctk.CTkLabel(attendance_frame, text="Attendance Record", font=('Helvetica', 16, 'bold'),
                                        text_color="#000080")
        attendance_label.pack(pady=5)
        for title, info in zip(["Time: ", "Count: ", "Location Status: ", "Scan Status: "], attendance_record):
            attendance_row = ctk.CTkFrame(attendance_frame, fg_color="#C0C0C0")
            attendance_row.pack(fill="x", padx=10, pady=2)

            title_label = ctk.CTkLabel(attendance_row, text=title, font=('Helvetica', 12, 'bold'), text_color="#404040")
            title_label.pack(side="left", padx=5)

            info_label = ctk.CTkLabel(attendance_row, text=info, font=('Helvetica', 12), text_color="blue")
            info_label.pack(side="left", padx=5)

    # Main content for image selection and reason entry
    info_frame = ctk.CTkFrame(upload_win, fg_color="white", corner_radius=10)
    info_frame.pack(side="right", expand=True, fill="both", padx=10, pady=10)

    # Image Preview Label
    image_label = Label(info_frame, bg='white')
    image_label.pack(pady=10)

    # Select Image Button
    ctk.CTkButton(info_frame, text="Select Image", fg_color="#8288FF", hover_color="#9BA5FF", command=select_image,
                  font=("Helvetica", 12)).pack(pady=10)

    # Reason Label and Text Box
    Label(info_frame, text="Enter Reason:", font=("Helvetica", 14, "bold"), bg="#f8f8f8").pack(pady=10)

    outline_frame = ctk.CTkFrame(info_frame, fg_color="black", corner_radius=10)
    outline_frame.pack(pady=10)

    reason_text = ctk.CTkTextbox(outline_frame, height=100, width=400, corner_radius=10)
    reason_text.pack(padx=3, pady=3)

    # Submit and Back Buttons
    ctk.CTkButton(info_frame, text="Submit", fg_color="#8288FF", hover_color="#9BA5FF", command=submit_evidence,
                  font=("Helvetica", 12)).pack(pady=20)
    ctk.CTkButton(info_frame, text="Back", fg_color="#00699E", hover_color="#0085C7", command=back,
                  font=("Helvetica", 12)).pack(pady=20)

def display_tenant_details(frame, assignment_id, tenant_id, attendance_record_id):
    # Clear previous content
    for widget in frame.winfo_children():
        widget.destroy()

    # Retrieve tenant information
    cursor.execute(
        "SELECT fullname, ic, date_of_birth, email_address, phone_number FROM tenant WHERE tenant_id = ?",
        (tenant_id,))
    tenant_info = cursor.fetchone()

    if tenant_info:
        tenant_frame = ctk.CTkFrame(frame)
        tenant_frame.pack(pady=3, fill="x")
        ctk.CTkLabel(tenant_frame, text="Tenant Information", font=("Helvetica", 16, "bold")).pack(pady=5)

        # Display tenant details in rows
        for title, info in zip(
                ["Full Name: ", "IC: ", "Date of Birth: ", "Email: ", "Phone Number: "],
                tenant_info
        ):
            row_frame = ctk.CTkFrame(tenant_frame)
            row_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row_frame, text=title, font=("Helvetica", 11, "bold")).pack(side="left")
            ctk.CTkLabel(row_frame, text=info, font=("Helvetica", 11), text_color='blue').pack(side="left")

    # Retrieve stall information
    cursor.execute(
        """
        SELECT stall_id, location, latitude, longitude 
        FROM stall 
        WHERE stall_id IN (SELECT stall_id FROM rental WHERE tenant_id = ?)
        """, (tenant_id,))
    stall_info = cursor.fetchone()

    if stall_info:
        stall_frame = ctk.CTkFrame(frame)
        stall_frame.pack(pady=3, fill="x")
        ctk.CTkLabel(stall_frame, text="Stall Information", font=("Helvetica", 16, "bold")).pack(pady=5)

        # Display stall details in rows
        for title, info in zip(
                ["Stall ID: ", "Location: ", "Latitude: ", "Longitude: "],
                stall_info
        ):
            row_frame = ctk.CTkFrame(stall_frame)
            row_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row_frame, text=title, font=("Helvetica", 11, "bold")).pack(side="left")
            ctk.CTkLabel(row_frame, text=info, font=("Helvetica", 11), text_color='blue').pack(side="left")

    # Retrieve attendance record information
    cursor.execute(
        """
        SELECT attendance_time, attendance_count, attendance_status, scan_status
        FROM attendance_records 
        WHERE attendance_records_id = ?
        """, (attendance_record_id,))
    attendance_record = cursor.fetchone()

    if attendance_record:
        attendance_frame = ctk.CTkFrame(frame)
        attendance_frame.pack(pady=3, fill="x")
        ctk.CTkLabel(attendance_frame, text="Attendance Record", font=("Helvetica", 16, "bold")).pack(pady=5)

        # Display attendance details in rows
        for title, info in zip(
                ["Time: ", "Count: ", "Location Status: ", "Scan Status: "],
                attendance_record
        ):
            row_frame = ctk.CTkFrame(attendance_frame)
            row_frame.pack(fill="x", padx=10, pady=2)
            ctk.CTkLabel(row_frame, text=title, font=("Helvetica", 11, "bold")).pack(side="left")
            ctk.CTkLabel(row_frame, text=info, font=("Helvetica", 11), text_color='blue').pack(side="left")
    else:
        attendance_frame = ctk.CTkFrame(frame)
        attendance_frame.pack(pady=5, fill="x")
        ctk.CTkLabel(attendance_frame, text="No attendance record found for this tenant.", fg_color="red").pack(pady=5)

    # Upload Evidence Button
    button_frame = ctk.CTkFrame(frame)
    button_frame.pack(pady=5, fill="x")
    ctk.CTkButton(
        button_frame, text="Upload Evidence", font=("Helvetica", 12), fg_color="#8288FF", hover_color="#9BA5FF",
        command=lambda: [assignments_win.destroy(), open_upload_window(assignment_id, tenant_id, attendance_record_id)]
    ).pack(pady=5)

def view_auditor_assignments():
    global assignments_win
    auditor_id = get_auditor_id_from_username(logged_in_user.get("username"))
    if auditor_id is None:
        return  # Exit if no auditor_id is found

    # Create a new window for viewing assignments
    assignments_win = Toplevel()
    assignments_win.title("Your Assigned Attendance Records")
    assignments_win.geometry("1920x1080+0+0")
    assignments_win.configure(bg="gray")
    assignments_win.state("zoomed")

    title_frame = ctk.CTkFrame(assignments_win, fg_color="white", corner_radius=10)
    title_frame.pack(side="top", fill="x", padx=10, pady=10)

    title_label = Label(title_frame, text="Assigned Assignment:", font=('Bauhaus 93', 24), bg="white", fg='#0016BA',
                        bd=15)
    title_label.pack(side='top', pady=5)

    info_frame = ctk.CTkFrame(assignments_win, fg_color="white", corner_radius=10)
    info_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)

    # Left frame for Treeview
    left_frame = Frame(info_frame, bg="#f8f8f8")
    left_frame.pack(side="left", fill="y", padx=10, pady=5)

    map_frame = Frame(left_frame, bg="#D3CAFF", padx=20, pady=10, bd=2, relief='groove')
    map_frame.pack(fill="x")

    # Right frame for tenant details
    right_frame = Frame(info_frame, bg="#f8f8f8")
    right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

    def back():
        """Close the upload window when 'Back' is clicked."""
        assignments_win.destroy()

    # Create a Treeview for displaying assignments
    columns = ("Assignment ID", "Tenant ID", "Attendance Record ID", "Assignment Date")
    tree = ttk.Treeview(left_frame, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
    tree.pack(side="left", fill="both", expand=True)

    # Scrollbar for Treeview
    scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # Retrieve auditor assignments based on auditor_id, excluding those in the evidence table
    cursor.execute("""
        SELECT assignment_id, tenant_id, attendance_records_id, assignment_date 
        FROM auditor_assignments 
        WHERE auditor_id = ? 
        AND assignment_id NOT IN (SELECT assignment_id FROM evidence)
    """, (auditor_id,))
    assignments = cursor.fetchall()

    for assignment in assignments:
        tree.insert("", "end", values=assignment)

    if not assignments:
        messagebox.showinfo("Info", "No assignments found for this auditor.")

    # Event to display tenant and attendance records in right panel on row selection
    def on_row_select(event):
        selected_item = tree.selection()
        if selected_item:
            values = tree.item(selected_item, "values")
            assignment_id = values[0]  # Get assignment_id from the selected row
            tenant_id = values[1]  # Get tenant_id from the selected row
            attendance_record_id = values[2]  # Get attendance_records_id from the selected row

            display_tenant_details(right_frame, assignment_id, tenant_id, attendance_record_id)
            auditor_open_map_view(map_frame, attendance_record_id)

    # Bind the event to row selection
    tree.bind("<<TreeviewSelect>>", on_row_select)

    # Add a frame at the bottom for the Back button, spanning both frames
    button_frame = ctk.CTkFrame(assignments_win, fg_color="#f8f8f8")
    button_frame.pack(side="bottom", fill="x", padx=10, pady=5)
    # Center the Back button within button_frame
    back_button = ctk.CTkButton(button_frame, text="Back", font=('times new roman', 18), fg_color="#00699E",
                                hover_color="#0085C7", text_color="white", command=assignments_win.destroy)
    back_button.pack(pady=10)

def auditor_open_map_view(map_frame, attendance_record_id):
    # Clear map_frame content
    for widget in map_frame.winfo_children():
        widget.destroy()

    # Map widget
    map_widget = TkinterMapView(map_frame, width=600, height=300, corner_radius=0)
    map_widget.pack(fill="both", expand=True)

    # Retrieve tenant and stall location
    try:
        cursor.execute("""
            SELECT tenant.fullname, attendance_records.latitude, attendance_records.longitude, 
                   attendance_records.attendance_status, attendance_records.scan_status, 
                   stall.stall_id, stall.latitude AS stall_lat, stall.longitude AS stall_lon
            FROM attendance_records
            JOIN tenant ON attendance_records.tenant_id = tenant.tenant_id
            JOIN stall ON attendance_records.stall_id = stall.stall_id
            WHERE attendance_records_id = ?
        """, (attendance_record_id,))
        record = cursor.fetchone()

        if record:
            fullname, tenant_lat, tenant_lon, attendance_status, scan_status, stall_id, stall_lat, stall_lon = record
            tenant_marker_text = f"Tenant: {fullname} -Stall ID: {stall_id}"

            # Set marker color
            marker_color = "yellow" if scan_status == "unrecognized" else (
                "green" if attendance_status == "Correct Location" else "red")

            # Set map marker for tenant location
            map_widget.set_position(tenant_lat, tenant_lon)
            map_widget.set_zoom(15)
            map_widget.set_marker(tenant_lat, tenant_lon, text=tenant_marker_text, marker_color_circle=marker_color,
                                  marker_color_outside=marker_color)

            # Add marker for stall location with stall ID, in blue
            stall_marker_text = f"Stall ID: {stall_id}"
            map_widget.set_marker(stall_lat, stall_lon, text=stall_marker_text, marker_color_circle="blue",
                                  marker_color_outside="blue")
        else:
            Label(map_frame, text="No map data available for this attendance record.", bg="#D3CAFF", fg="red").pack(
                pady=10)
    except sqlite3.OperationalError as e:
        messagebox.showerror("Database Error", f"Error fetching data: {e}")

# List to store icon images to prevent garbage collection
icon_images = []
def auditor_dashboard():
    def logout():
        result = messagebox.askquestion('System', 'Are you sure you want to logout?', icon="warning")
        if result == 'yes':
            auditor_win.destroy()
            form_frame.deiconify()

    root.withdraw()
    form_frame.withdraw()

    auditor_win = Toplevel()
    auditor_win.title("Auditor Dashboard")
    auditor_win.geometry("1920x1080+0+0")
    auditor_win.state("zoomed")
    auditor_win.configure(bg="gray")

    # Header Frame for the dashboard title
    header_frame = ctk.CTkFrame(auditor_win, height=100, fg_color="#343a40")
    header_frame.pack(fill="x")

    title_label = ctk.CTkLabel(header_frame, text="Auditor Dashboard", font=("Bauhaus 93", 24),
                               text_color="white")
    title_label.pack(pady=20)

    # Title frame for animated welcome message
    title_frame = ctk.CTkFrame(auditor_win, fg_color="white", corner_radius=20)
    title_frame.pack(side="top", fill="x", padx=10, pady=(10, 0))

    title2_label = ctk.CTkLabel(title_frame, text="", font=('Algerian', 26, 'bold'), text_color='#0016BA')
    title2_label.pack(side='top', pady=10)

    # Define the full text for animation
    full_text = "WELCOME TO GOVERNMENT STALL RENTAL SYSTEM:"

    def animate_text(index=0):
        if index < len(full_text):
            title2_label.configure(text=full_text[:index + 1])
            title2_label.after(150, animate_text, index + 1)
        else:
            title2_label.after(1000, animate_text, 0)

    animate_text()

    # Load and display the background image
    background_image = Image.open("image\\auditor_bg.png")
    background_image = background_image.resize((1500, 650), Image.Resampling.LANCZOS)
    background_photo = ImageTk.PhotoImage(background_image)

    # Canvas for the image and overlayed icons/text
    canvas = Canvas(auditor_win, width=1500, height=650, highlightthickness=0)
    canvas.pack(expand=True, fill="both", padx=20, pady=20)

    # Display the background image on the canvas
    canvas.create_image(0, 0, image=background_photo, anchor="nw")
    canvas.background_photo = background_photo  # Keep a reference to prevent garbage collection

    # Add icons and labels for each triangle section
    def create_overlay(x, y, icon_path, text, command):
        # Load the icon image
        icon_image = Image.open(icon_path)
        icon_image = icon_image.resize((50, 50), Image.Resampling.LANCZOS)
        icon_photo = ImageTk.PhotoImage(icon_image)

        # Store the icon image in the icon_images list to prevent garbage collection
        icon_images.append(icon_photo)

        # Place icon on the canvas
        icon_id = canvas.create_image(x, y, image=icon_photo, anchor="center")

        # Place text under the icon
        text_id = canvas.create_text(x, y + 45, text=text, font=("Helvetica", 20, "bold"), fill="white")

        # Bind click events to both the icon and text
        canvas.tag_bind(icon_id, "<Button-1>", lambda event: command())
        canvas.tag_bind(text_id, "<Button-1>", lambda event: command())

        # Optionally add hover effects
        def on_enter(event):
            canvas.itemconfig(text_id, fill="#AEABFF")  # Change text color on hover

        def on_leave(event):
            canvas.itemconfig(text_id, fill="white")  # Revert text color when not hovering

        canvas.tag_bind(icon_id, "<Enter>", on_enter)
        canvas.tag_bind(icon_id, "<Leave>", on_leave)
        canvas.tag_bind(text_id, "<Enter>", on_enter)
        canvas.tag_bind(text_id, "<Leave>", on_leave)

    # Position each icon and label text in the appropriate triangular section
    # Use your own icons paths here
    create_overlay(980, 100, "image\\view_tenants.png", "View Assignments", view_auditor_assignments)
    create_overlay(1400, 200, "image\\notification.png", "Notifications", show_notifications)
    create_overlay(1200, 400, "image\\profiles.png", "Profiles", auditor_profile)
    create_overlay(1430, 550, "image\\logout.png", "Logout", logout)



def show_notifications():
    # Create a new window for the auditor notifications
    auditor_window = Toplevel()
    auditor_window.title("Auditor Notifications")
    auditor_window.geometry("1920x1080+0+0")
    auditor_window.state("zoomed")
    auditor_window.config(bg="#C7D3FF")

    # Header frame
    header_frame = ctk.CTkFrame(auditor_window, fg_color="#003366", height=60)
    header_frame.pack(fill='x')
    ctk.CTkLabel(header_frame, text="Auditor Notifications", font=("Bauhaus 93", 28), text_color="white").pack(pady=15)

    # Create a frame for notifications
    notification_frame = ctk.CTkFrame(auditor_window, fg_color="#C7D3FF", corner_radius=10)
    notification_frame.pack(fill='both', expand=True, padx=20, pady=20)

    # Frame for Treeview and message display
    notification_content_frame = ctk.CTkFrame(notification_frame, fg_color="#C7D3FF")
    notification_content_frame.pack(fill='both', expand=True)

    # Frame for Treeview and scrollbar
    table_frame = ctk.CTkFrame(notification_content_frame, fg_color="#C7D3FF")
    table_frame.pack(side='left', fill='both', expand=True)

    # Use ttk.Treeview for the notification table
    notification_table = ttk.Treeview(table_frame, columns=("Date",), show='headings', height=20)
    notification_table.pack(side='left', fill='both', expand=True)
    notification_table.heading("Date", text="Date")
    notification_table.column("Date", width=150)

    # Scrollbar for the Treeview
    scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=notification_table.yview)
    scrollbar.pack(side='right', fill='y')
    notification_table.configure(yscrollcommand=scrollbar.set)

    # Text widget to display selected message
    message_display = ctk.CTkTextbox(notification_content_frame, height=20, wrap="word", state="disabled")
    message_display.pack(side='right', fill='both', expand=True, padx=10, pady=10)

    # Row selection handler
    def on_row_select(event):
        selected_item = notification_table.selection()
        if selected_item:
            notification_id = notification_table.item(selected_item, 'tags')[0]
            cursor.execute("SELECT message FROM notification WHERE notification_id = ?", (notification_id,))
            message = cursor.fetchone()
            if message:
                message_display.configure(state="normal")
                message_display.delete("1.0", "end")
                message_display.insert("1.0", message[0])
                message_display.configure(state="disabled")

    notification_table.bind("<<TreeviewSelect>>", on_row_select)

    # Variables for "No notifications available" label and flag
    message_displayed = False
    no_notifications_label = None

    def twinkle_label():
        if no_notifications_label:
            current_color = no_notifications_label.cget("fg")
            new_color = "#FF0000" if current_color == "#C7D3FF" else "#C7D3FF"
            no_notifications_label.config(fg=new_color)
            no_notifications_label.after(500, twinkle_label)

    def load_notifications(show_history=False):
        nonlocal message_displayed, no_notifications_label
        notification_table.delete(*notification_table.get_children())
        message_display.configure(state="normal")
        message_display.delete("1.0", "end")
        message_display.configure(state="disabled")

        if no_notifications_label:
            no_notifications_label.destroy()
            no_notifications_label = None

        try:
            username = logged_in_user.get("username")
            cursor.execute("SELECT auditor_id FROM auditor WHERE username = ?", (username,))
            auditor = cursor.fetchone()

            if auditor:
                auditor_id = auditor[0]
                query = """ 
                        SELECT notification_id, notification_date FROM notification 
                        WHERE recipient = 'auditor' AND recipient_id = ? AND is_read = ?
                        ORDER BY notification_date DESC
                    """
                cursor.execute(query, (auditor_id, 1 if show_history else 0))
                notifications = cursor.fetchall()

                if not show_history:
                    cursor.execute(""" 
                            UPDATE notification SET is_read = 1
                            WHERE recipient = 'auditor' AND recipient_id = ?
                        """, (auditor_id,))
                conn.commit()

                message_displayed = False
                if notifications:
                    for notification_id, notification_date in notifications:
                        notification_table.insert("", "end", values=(notification_date,), tags=(notification_id,))
                else:
                    if not message_displayed:
                        no_notifications_label = Label(notification_frame, text="No notifications available.",
                                                       font=("Arial", 14), fg="#FF0000", bg="#C7D3FF")
                        no_notifications_label.pack(pady=10)
                        message_displayed = True
                        twinkle_label()
            else:
                Label(notification_frame, text="User not found.", font=("Arial", 14), bg="#99ccff").pack(pady=10)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error retrieving notifications: {e}")

    # Toggle between unread and history notifications
    show_history_var = ctk.BooleanVar(value=False)
    toggle_button = ctk.CTkCheckBox(notification_frame, text="Show Read Notifications", variable=show_history_var,
                                    font=("Arial", 12), command=lambda: load_notifications(show_history_var.get()))
    toggle_button.pack(pady=10)

    # Load unread notifications initially
    load_notifications(show_history=False)

    # Footer frame with Back button
    footer_frame = ctk.CTkFrame(auditor_window, fg_color="#003366", height=60)
    footer_frame.pack(fill='x', side='bottom')
    ctk.CTkButton(footer_frame, text="Back", font=("Arial", 16), text_color="white", fg_color="#8288FF",
                  hover_color="#9BA5FF",
                  command=auditor_window.destroy).pack(pady=10)

def auditor_profile():
    # Create a new window for the auditor profile
    def open_edit_auditor_info_and_close_dashboard(event=None):
        profile_window.destroy()
        edit_auditor_info()

    profile_window = Toplevel()
    profile_window.title("Auditor Profile")
    profile_window.geometry("800x600")  # Set the size of the new window
    profile_window.configure(bg="#C7D3FF")

    # Set up a frame for the auditor profile
    profile_frame = Frame(profile_window, bg="#C7D3FF", padx=20, bd=2, relief='groove')
    profile_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Title for the auditor profile
    title_label = Label(profile_frame, text="Auditor Profile", bg="#C7D3FF", font=("Bauhaus 93", 24, "bold"),
                        fg="black")
    title_label.pack(pady=10, anchor='center')

    # Assuming logged_in_user has the auditor's username
    username = logged_in_user.get('username')

    if username:
        # Retrieve auditor information from the database
        cursor.execute("SELECT * FROM auditor WHERE username = ?", (username,))
        auditor_info = cursor.fetchone()

        if auditor_info:
            auditor_id, username, password, fullname, ic, date_of_birth, email_address, phone_number, face_id_image, face_embedding = auditor_info

            # Create a frame for holding the image and info side by side, centered
            main_frame = ctk.CTkFrame(profile_frame, fg_color="#CFCFCF", border_color="#A8A8A8", border_width=2)
            main_frame.pack(pady=20, anchor='center')

            # Create a frame for the face image
            face_frame = Frame(main_frame, bg="#CFCFCF")
            face_frame.pack(side='left', padx=20, pady=20)

            # Display the profile image at the top (if available)
            profile_image_label = Label(face_frame, bg="#CFCFCF")
            profile_image_label.pack()

            if face_id_image:
                try:
                    # Open the profile image
                    img = Image.open(face_id_image)
                    img = img.resize((280, 280), Image.Resampling.LANCZOS)  # Resize as needed
                    profile_img = ImageTk.PhotoImage(img)

                    profile_image_label.config(image=profile_img)
                    profile_image_label.image = profile_img  # Keep a reference to avoid garbage collection

                except Exception as e:
                    print(f"Error loading image: {e}")
                    profile_image_label.config(text="Profile image not found.", bg="#C7D3FF")

            # Create a frame for tenant information
            info_frame = ctk.CTkFrame(main_frame, fg_color="#CFCFCF", border_color="#A8A8A8", border_width=2)
            info_frame.pack(side='left', padx=20)

            # Display tenant information with labels and values beside each other
            def add_info_row(label_text, value_text):
                row_frame = Frame(info_frame, bg="#CFCFCF")
                row_frame.pack(anchor='w', padx=20, pady=5)
                Label(row_frame, text=label_text, bg="#CFCFCF", font=("Arial", 12, 'bold')).pack(side='left')
                Label(row_frame, text=value_text, bg="#CFCFCF", fg="blue", font=("Arial", 12)).pack(side='left')

            add_info_row("Username: ", username)
            add_info_row("Full Name: ", fullname)
            add_info_row("IC: ", ic)
            add_info_row("Date of Birth: ", str(date_of_birth))
            add_info_row("Email: ", email_address)
            add_info_row("Phone Number: ", phone_number)

            # Edit button for updating auditor information
            edit_button = ctk.CTkButton(profile_frame, text="Edit Information", font=("Arial", 20, "bold"),
                                        fg_color='#00527B', text_color='white', corner_radius=50,
                                        command=open_edit_auditor_info_and_close_dashboard)
            edit_button.pack(pady=10, anchor='center')

        else:
            Label(profile_frame, text="Auditor not found.", bg="#C7D3FF", font=("Arial", 12)).pack(pady=10)
    else:
        Label(profile_frame, text="No user is logged in.", bg="#C7D3FF", font=("Arial", 12)).pack(pady=10)

def edit_auditor_info():
    global password_entry, eye_button, eye_open_image, eye_closed_image

    # Function to fetch auditor data from the database
    def fetch_auditor_data():
        conn = sqlite3.connect("stall_rental_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, email_address, phone_number, password FROM auditor WHERE username = ?",
                       (logged_in_user['username'],))
        auditor_data = cursor.fetchone()
        conn.close()  # Close the connection
        return auditor_data

    # Function to update auditor data in the database
    def update_auditor_data(new_username, new_email_address, new_phone_number, new_password):
        conn = sqlite3.connect("stall_rental_system.db")
        cursor = conn.cursor()
        try:
            # Check if the new username is already in use by another auditor
            cursor.execute("SELECT username FROM auditor WHERE username = ? AND username != ?",
                           (new_username, logged_in_user['username']))
            existing_auditor = cursor.fetchone()

            if existing_auditor:
                messagebox.showerror("Username Error",
                                     "Username already exists. Please choose a different username.")
                return False

            # Update auditor data
            cursor.execute(
                "UPDATE auditor SET username = ?, email_address = ?, phone_number = ?, password = ? WHERE username = ?",
                (new_username, new_email_address, new_phone_number, new_password, logged_in_user['username'])
            )
            conn.commit()

            # Update logged_in_user
            logged_in_user['username'] = new_username
            logged_in_user['password'] = new_password

            return True

        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            return False
        finally:
            conn.close()  # Ensure the connection is closed

    # Function to load auditor data into labels and allow editing
    def load_auditor_data_view():
        auditor_data = fetch_auditor_data()
        if auditor_data:
            username_var.set(auditor_data[0])
            email_address_var.set(auditor_data[1])
            phone_number_var.set(auditor_data[2])
            password_var.set(auditor_data[3])

    # Function to save auditor data
    def save_auditor_data():
        username = username_var.get()
        email_address = email_address_var.get()
        phone_number = phone_number_var.get()
        password = password_var.get()

        if update_auditor_data(username, email_address, phone_number, password):
            load_auditor_data_view()
            messagebox.showinfo("Success", "Auditor information updated successfully!")
        else:
            load_auditor_data_view()

    # Function to toggle between edit and save modes
    def toggle_edit_save():
        nonlocal is_edit_mode
        if is_edit_mode:
            # Save the data and disable entries
            save_auditor_data()
            toggle_entry_state(DISABLED)
            edit_save_button.config(text="Edit")
        else:
            # Enable the entries for editing
            toggle_entry_state(NORMAL)
            edit_save_button.config(text="Save")

        is_edit_mode = not is_edit_mode

    # Function to toggle the state of entry fields
    def toggle_entry_state(state):
        username_entry.config(state=state)
        email_address_entry.config(state=state)
        phone_number_entry.config(state=state)
        password_entry.config(state=state)

    def close_edit_window():
        edit_window.destroy()

    # Create and display the auditor info edit window
    edit_window = Toplevel()
    edit_window.title("Auditor Information")
    edit_window.geometry("1920x1080+0+0")  # window size and position
    edit_window.state("zoomed")

    # Load the background image
    image = Image.open("image\\bg3.png").convert("RGBA")
    resized_image = image.resize((1920, 1080), Image.Resampling.LANCZOS)
    alpha = 180  # Transparency level
    alpha_channel = resized_image.split()[3].point(lambda p: p * alpha / 255.)
    transparent_image = Image.merge("RGBA", (resized_image.split()[:3] + (alpha_channel,)))

    # Convert the image to a format tkinter can handle
    bg2_image = ImageTk.PhotoImage(transparent_image)

    # Create a canvas to hold the image and text
    canvas = Canvas(edit_window, width=1920, height=1080)
    canvas.place(x=0, y=0, relwidth=1, relheight=1)

    # Place the background image on the canvas
    canvas.create_image(0, 0, anchor='nw', image=bg2_image)

    is_edit_mode = False  # Toggle edit/save mode

    # Create entry variables
    username_var = StringVar()
    email_address_var = StringVar()
    phone_number_var = StringVar()
    password_var = StringVar()

    # Load auditor data into the entry variables
    load_auditor_data_view()

    # Create and pack the title label on the canvas
    canvas.create_text(770, 50, text="Auditor Information", font=('Algerian', 26, 'bold'), fill="black")

    # Create labels and entry fields on the canvas
    canvas.create_text(620, 150, text="Username:", font=('Arial', 16, 'bold'), fill="black")
    username_entry = Entry(edit_window, textvariable=username_var, font=('Arial', 16), highlightbackground="black",
                           highlightcolor="black", highlightthickness=2)
    canvas.create_window(870, 150, window=username_entry, width=300)

    canvas.create_text(620, 220, text="Email Address:", font=('Arial', 16, 'bold'), fill="black")
    email_address_entry = Entry(edit_window, textvariable=email_address_var, font=('Arial', 16),
                                highlightbackground="black", highlightcolor="black", highlightthickness=2)
    canvas.create_window(870, 220, window=email_address_entry, width=300)

    canvas.create_text(620, 290, text="Phone Number:", font=('Arial', 16, 'bold'), fill="black")
    phone_number_entry = Entry(edit_window, textvariable=phone_number_var, font=('Arial', 16),
                               highlightbackground="black", highlightcolor="black", highlightthickness=2)
    canvas.create_window(870, 290, window=phone_number_entry, width=300)

    canvas.create_text(620, 360, text="Password:", font=('Arial', 16, 'bold'), fill="black")
    password_entry = Entry(edit_window, textvariable=password_var, show='*', font=('Arial', 16),
                           highlightbackground="black", highlightcolor="black", highlightthickness=2)
    canvas.create_window(870, 360, window=password_entry, width=300)

    eye_open_image = ImageTk.PhotoImage(Image.open("image\\open_eye.png").resize((25, 25)))
    eye_closed_image = ImageTk.PhotoImage(Image.open("image\\closed_eye.png").resize((25, 25)))

    # Create and place the eye button
    eye_button = Button(edit_window, image=eye_closed_image, command=toggle_password_visibility, bg='white',
                        borderwidth=0)
    canvas.create_window(1002, 360, window=eye_button, width=30)

    # Create and place the Edit/Save button
    edit_save_button = Button(edit_window, text="Edit", command=toggle_edit_save, font=('Arial', 16, 'bold'),
                              bg='#8EDE7E', fg='white')
    edit_save_button.bind("<Enter>", lambda e: edit_save_button.configure(bg="#98ED86"))
    edit_save_button.bind("<Leave>", lambda e: edit_save_button.configure(bg="#8EDE7E"))
    canvas.create_window(770, 450, window=edit_save_button, width=150)

    # Create and place the Close button
    close_button = Button(edit_window, text="Close", command=close_edit_window, font=('Arial', 16, 'bold'),
                          bg='#E3807D', fg='white')
    close_button.bind("<Enter>", lambda e: close_button.configure(bg="#F28885"))
    close_button.bind("<Leave>", lambda e: close_button.configure(bg="#E3807D"))
    canvas.create_window(770, 510, window=close_button, width=150)

    # Initially disable the entry fields
    toggle_entry_state(DISABLED)
    edit_window.image = bg2_image

def toggle_password_visibility():
    """Toggle password visibility."""
    if password_entry.cget('show') == '*':
        password_entry.config(show='')
        eye_button.config(image=eye_open_image)
    else:
        password_entry.config(show='*')
        eye_button.config(image=eye_closed_image)



# Admin
def admin_dashboard():
    global content_frame

    def update_selected_category(category):
        selected_category.set(category)
        top_canvas.itemconfig(selected_category_text_id, text=selected_category.get())

        # Call the appropriate admin function based on the selected category
        if category == "Manage Stalls":
            stalls_admin()
        elif category == "Tenants":
            tenant_part()
        elif category == "Auditor":
            auditor_part()
        elif category == "Reports":
            generate_report()
        elif category == "Notification":
            admin_notification()
        elif category == "Profile":
            admin_profile()

    # Function to toggle visibility of categories
    def toggle_categories():
        if category_frame.winfo_viewable():
            category_frame.pack_forget()
            toggle_category_btn.configure(image=open_icon)
            content_frame.pack(side='right', fill='both', expand=True)
            create_collapsed_icons()
        else:
            collapsed_icon_frame.pack_forget()
            category_frame.pack(side='left', fill='y')
            toggle_category_btn.configure(image=close_icon)
            content_frame.pack(side='right', fill='both', expand=True)

    # Function to create collapsed icons
    def create_collapsed_icons():
        for widget in collapsed_icon_frame.winfo_children():
            widget.destroy()

        # Create toggle button for collapsed icons
        toggle_category_btn = Button(collapsed_icon_frame, image=open_icon, command=toggle_categories, bg='black',
                                     borderwidth=0)
        toggle_category_btn.pack(side='top', pady=10)

        # Determine current theme to set colors
        current_bg = admin_window.cget('bg')
        icon_bg_color = "#C3C3C3" if current_bg == "#f8f8f8" else "#696969"

        for index, category in enumerate(categories):
            # Create category icon labels with appropriate background color
            category_icon_label = Label(collapsed_icon_frame, image=category_icons[category], bg=icon_bg_color)
            category_icon_label.pack(side='top', padx=10, pady=10)
            category_icon_label.bind("<Button-1>", lambda event, c=category: update_selected_category(c))

        # Create logout icon label with appropriate background color
        logout_icon_label = Label(collapsed_icon_frame, image=logout_icon, bg=icon_bg_color)
        logout_icon_label.pack(side='bottom', padx=10, pady=10)
        logout_icon_label.bind("<Button-1>", lambda event: logout())

        collapsed_icon_frame.pack(side='left', fill='y')

    def toggle_theme():
        current_bg = admin_window.cget('bg')
        if current_bg == "#f8f8f8":
            # Dark theme
            admin_window.configure(bg="#2c2c2c")
            top_canvas.configure(bg="#2c2c2c")
            content_frame.configure(bg="#2c2c2c")
            category_frame.configure(bg="#696969")
            collapsed_icon_frame.configure(bg="#696969")

            # Update category button colors
            for btn in category_buttons:
                btn.configure(bg="#858585", fg='white')

            # Update logout button colors
            logout_btn.configure(bg="#858585", fg='white')

            # Update category icon labels for dark theme
            for category_icon_label in collapsed_icon_frame.winfo_children():
                if isinstance(category_icon_label, Label):
                    category_icon_label.configure(bg="#696969")

            # Update logout icon label for dark theme
            for widget in collapsed_icon_frame.winfo_children():
                if isinstance(widget, Label) and widget.cget('image') == str(logout_icon):
                    widget.configure(bg="#696969")

            # Update icons for dark mode
            toggle_theme_btn.configure(image=dark_mode_icon)

        else:
            # Light theme
            admin_window.configure(bg="#f8f8f8")
            top_canvas.configure(bg="black")
            content_frame.configure(bg="#f8f8f8")
            category_frame.configure(bg="#C3C3C3")
            collapsed_icon_frame.configure(bg="#C3C3C3")

            # Update category button colors
            for btn in category_buttons:
                btn.configure(bg="#919191", fg='black')

            # Update logout button colors
            logout_btn.configure(bg='#919191', fg='black')

            # Update category icon labels for light theme
            for category_icon_label in collapsed_icon_frame.winfo_children():
                if isinstance(category_icon_label, Label):
                    category_icon_label.configure(bg="#C3C3C3")

            # Update logout icon label for light theme
            for widget in collapsed_icon_frame.winfo_children():
                if isinstance(widget, Label) and widget.cget('image') == str(logout_icon):
                    widget.configure(bg="#C3C3C3")

            # Update icons for light mode
            toggle_theme_btn.configure(image=light_mode_icon)

    def logout():
        result = messagebox.askquestion('System', 'Are you sure you want to logout?', icon="warning")
        if result == 'yes':
            admin_window.destroy()
            form_frame.deiconify()

    def open_edit_user_info_and_close_dashboard(event=None):
        admin_window.destroy()
        edit_admin_info()

    def admin_profile():
        # Clear the content frame
        for widget in content_frame.winfo_children():
            widget.destroy()

        # Set up a frame for the admin profile
        profile_frame = Frame(content_frame, bg="#C7D3FF", padx=20, bd=2, relief='groove')
        profile_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Title for the admin profile
        title_label = Label(profile_frame, text="Admin Profile", bg="#C7D3FF", font=("Bauhaus 93", 24, "bold"),
                            fg="black")
        title_label.pack(pady=10, anchor='center')

        # Assuming logged_in_user has the admin's username
        username = logged_in_user.get('username')

        if username:
            # Retrieve admin information from the database
            cursor.execute("SELECT * FROM admin WHERE username = ?", (username,))
            admin_info = cursor.fetchone()

            if admin_info:
                admin_id, username, password, fullname, ic, date_of_birth, email_address, phone_number, face_id_image, face_embedding = admin_info

                # Create a frame for holding the image and info side by side, centered
                main_frame = ctk.CTkFrame(profile_frame, fg_color="#CFCFCF", border_color="#A8A8A8", border_width=2)
                main_frame.pack(pady=20, anchor='center')

                # Create a frame for the face image
                face_frame = Frame(main_frame, bg="#CFCFCF")
                face_frame.pack(side='left', padx=20, pady=20)

                # Display the profile image at the top (if available)
                profile_image_label = Label(face_frame, bg="#CFCFCF")
                profile_image_label.pack()

                if face_id_image:
                    try:
                        # Open the profile image
                        img = Image.open(face_id_image)
                        img = img.resize((280, 280), Image.Resampling.LANCZOS)  # Resize as needed
                        profile_img = ImageTk.PhotoImage(img)

                        profile_image_label.config(image=profile_img)
                        profile_image_label.image = profile_img  # Keep a reference to avoid garbage collection

                    except Exception as e:
                        print(f"Error loading image: {e}")
                        profile_image_label.config(text="Profile image not found.", bg="#C7D3FF")

                # Create a frame for tenant information
                info_frame = ctk.CTkFrame(main_frame, fg_color="#CFCFCF", border_color="#A8A8A8",
                                                  border_width=2)
                info_frame.pack(side='left', padx=20)

                 # Display tenant information with labels and values beside each other
                def add_info_row(label_text, value_text):
                    row_frame = Frame(info_frame, bg="#CFCFCF")
                    row_frame.pack(anchor='w', padx=20, pady=5)
                    Label(row_frame, text=label_text, bg="#CFCFCF", font=("Arial", 12, 'bold')).pack(
                                side='left')
                    Label(row_frame, text=value_text, bg="#CFCFCF", fg="blue", font=("Arial", 12)).pack(
                                side='left')

                add_info_row("Username: ", username)
                add_info_row("Full Name: ", fullname)
                add_info_row("IC: ", ic)
                add_info_row("Date of Birth: ", str(date_of_birth))
                add_info_row("Email: ", email_address)
                add_info_row("Phone Number: ", phone_number)

                # Edit button for updating admin information
                edit_button = ctk.CTkButton(profile_frame, text="Edit Information", font=("Arial", 20, "bold"),
                                            fg_color='#00527B', text_color='white', corner_radius=50,
                                            command=open_edit_user_info_and_close_dashboard)
                edit_button.bind("<Enter>", lambda e: edit_button.configure(fg_color="#0070A8"))
                edit_button.bind("<Leave>", lambda e: edit_button.configure(fg_color="#00527B"))
                edit_button.pack(pady=10, anchor='center')

            else:
                Label(profile_frame, text="Admin not found.", bg="#C7D3FF", font=("Arial", 12)).pack(pady=10)
        else:
            Label(profile_frame, text="No user is logged in.", bg="#C7D3FF", font=("Arial", 12)).pack(pady=10)

    def edit_admin_info():
        global password_entry, eye_button, eye_open_image, eye_closed_image

        # Function to fetch admin data from the database
        def fetch_admin_data():
            conn = sqlite3.connect("stall_rental_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT username, email_address, phone_number, password FROM admin WHERE username = ?",
                           (logged_in_user['username'],))
            admin_data = cursor.fetchone()
            return admin_data

        # Function to update admin data in the database
        def update_admin_data(new_username, new_email_address, new_phone_number, new_password):
            conn = sqlite3.connect("stall_rental_system.db")
            cursor = conn.cursor()
            try:
                # Check if the new username is already in use by another admin
                cursor.execute("SELECT username FROM admin WHERE username = ? AND username != ?",
                               (new_username, logged_in_user['username']))
                existing_admin = cursor.fetchone()

                if existing_admin:
                    messagebox.showerror("Username Error",
                                         "Username already exists. Please choose a different username.")
                    return False

                # Update admin data
                cursor.execute(
                    "UPDATE admin SET username = ?, email_address = ?, phone_number = ?, password = ? WHERE username = ?",
                    (new_username, new_email_address, new_phone_number, new_password, logged_in_user['username'])
                )
                conn.commit()

                # Update logged_in_user
                logged_in_user['username'] = new_username
                logged_in_user['password'] = new_password

                return True

            except sqlite3.Error as e:
                print(f"SQLite error: {e}")
                return False

        # Function to load admin data into labels and allow editing
        def load_admin_data_view():
            admin_data = fetch_admin_data()
            if admin_data:
                username_var.set(admin_data[0])
                email_address_var.set(admin_data[1])
                phone_number_var.set(admin_data[2])
                password_var.set(admin_data[3])

        # Function to save admin data
        def save_admin_data():
            username = username_var.get()
            email_address = email_address_var.get()
            phone_number = phone_number_var.get()
            password = password_var.get()

            if update_admin_data(username, email_address, phone_number, password):
                load_admin_data_view()
                messagebox.showinfo("Success", "Admin information updated successfully!")
            else:
                load_admin_data_view()

        # Function to toggle between edit and save modes
        def toggle_edit_save():
            nonlocal is_edit_mode
            if is_edit_mode:
                # Save the data and disable entries
                save_admin_data()
                toggle_entry_state(DISABLED)
                edit_save_button.config(text="Edit")
            else:
                # Enable the entries for editing
                toggle_entry_state(NORMAL)
                edit_save_button.config(text="Save")

            is_edit_mode = not is_edit_mode

        # Function to toggle the state of entry fields
        def toggle_entry_state(state):
            username_entry.config(state=state)
            email_address_entry.config(state=state)
            phone_number_entry.config(state=state)
            password_entry.config(state=state)

        def close_edit_window():
            edit_window.destroy()
            admin_dashboard()  # Return to admin dashboard

        # Create and display the admin info edit window
        edit_window = Toplevel()
        edit_window.title("Admin Information")
        edit_window.geometry("1920x1080+0+0")  # window size and position
        edit_window.state("zoomed")

        # Load the background image
        image = Image.open("image\\bg3.png").convert("RGBA")
        resized_image = image.resize((1920, 1080), Image.Resampling.LANCZOS)
        alpha = 180  # Transparency level
        alpha_channel = resized_image.split()[3].point(lambda p: p * alpha / 255.)
        transparent_image = Image.merge("RGBA", (resized_image.split()[:3] + (alpha_channel,)))

        # Convert the image to a format tkinter can handle
        bg2_image = ImageTk.PhotoImage(transparent_image)

        # Create a canvas to hold the image and text
        canvas = Canvas(edit_window, width=1920, height=1080)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Place the background image on the canvas
        canvas.create_image(0, 0, anchor='nw', image=bg2_image)

        is_edit_mode = False  # Toggle edit/save mode

        # Create entry variables
        username_var = StringVar()
        email_address_var = StringVar()
        phone_number_var = StringVar()
        password_var = StringVar()

        # Load admin data into the entry variables
        load_admin_data_view()

        # Create and pack the title label on the canvas
        canvas.create_text(770, 50, text="Admin Information", font=('Algerian', 26, 'bold'), fill="black")

        # Create labels and entry fields on the canvas
        canvas.create_text(620, 150, text="Username:", font=('Arial', 16, 'bold'), fill="black")
        username_entry = Entry(edit_window, textvariable=username_var, font=('Arial', 16), highlightbackground="black",
                               highlightcolor="black", highlightthickness=2)
        canvas.create_window(870, 150, window=username_entry, width=300)

        canvas.create_text(620, 220, text="Email Address:", font=('Arial', 16, 'bold'), fill="black")
        email_address_entry = Entry(edit_window, textvariable=email_address_var, font=('Arial', 16),
                                    highlightbackground="black", highlightcolor="black", highlightthickness=2)
        canvas.create_window(870, 220, window=email_address_entry, width=300)

        canvas.create_text(620, 290, text="Phone Number:", font=('Arial', 16, 'bold'), fill="black")
        phone_number_entry = Entry(edit_window, textvariable=phone_number_var, font=('Arial', 16),
                                   highlightbackground="black", highlightcolor="black", highlightthickness=2)
        canvas.create_window(870, 290, window=phone_number_entry, width=300)

        canvas.create_text(620, 360, text="Password:", font=('Arial', 16, 'bold'), fill="black")
        password_entry = Entry(edit_window, textvariable=password_var, show='*', font=('Arial', 16),
                               highlightbackground="black", highlightcolor="black", highlightthickness=2)
        canvas.create_window(870, 360, window=password_entry, width=300)

        eye_open_image = ImageTk.PhotoImage(Image.open("image\\open_eye.png").resize((25, 25)))
        eye_closed_image = ImageTk.PhotoImage(Image.open("image\\closed_eye.png").resize((25, 25)))

        # Create and place the eye button
        eye_button = Button(edit_window, image=eye_closed_image, command=toggle_password_visibility, bg='white',
                            borderwidth=0)
        canvas.create_window(1002, 360, window=eye_button, width=30)

        # Create and place the Edit/Save button
        edit_save_button = Button(edit_window, text="Edit", command=toggle_edit_save, font=('Arial', 16, 'bold'),
                                  bg='#8EDE7E', fg='white')
        edit_save_button.bind("<Enter>", lambda e: edit_save_button.configure(bg="#98ED86"))
        edit_save_button.bind("<Leave>", lambda e: edit_save_button.configure(bg="#8EDE7E"))
        canvas.create_window(770, 450, window=edit_save_button, width=150)

        # Create and place the Close button
        close_button = Button(edit_window, text="Close", command=close_edit_window, font=('Arial', 16, 'bold'),
                              bg='#E3807D', fg='white')
        close_button.bind("<Enter>", lambda e: close_button.configure(bg="#F28885"))
        close_button.bind("<Leave>", lambda e: close_button.configure(bg="#E3807D"))
        canvas.create_window(770, 510, window=close_button, width=150)

        # Initially disable the entry fields
        toggle_entry_state(DISABLED)
        edit_window.image = bg2_image

    def toggle_password_visibility():
        """Toggle password visibility."""
        if password_entry.cget('show') == '*':
            password_entry.config(show='')
            eye_button.config(image=eye_open_image)
        else:
            password_entry.config(show='*')
            eye_button.config(image=eye_closed_image)

    root.withdraw()
    form_frame.withdraw()

    admin_window = Toplevel()
    admin_window.title("Admin Dashboard")
    admin_window.geometry("1920x1080+0+0")
    admin_window.state("zoomed")
    admin_window.configure(bg="#f8f8f8")

    gif_image_path = "image\\light3.gif"
    gif_image = Image.open(gif_image_path)
    desired_width, desired_height = 1920, 1080
    gif_frames = []

    try:
        while True:
            resized_frame = gif_image.resize((desired_width, desired_height), Image.Resampling.LANCZOS)
            gif_frame = ImageTk.PhotoImage(resized_frame)
            gif_frames.append(gif_frame)
            gif_image.seek(len(gif_frames))
    except EOFError:
        pass

    gif_frames_count = len(gif_frames)

    top_canvas = Canvas(admin_window, width=1920, height=150, bg="black", highlightbackground="black",
                        highlightcolor="black", highlightthickness=2)
    top_canvas.pack(fill='x')

    gif_image_id = top_canvas.create_image(0, 0, image=gif_frames[0], anchor='nw')

    def animate_gif(frame_index):
        top_canvas.itemconfig(gif_image_id, image=gif_frames[frame_index])
        frame_index = (frame_index + 1) % gif_frames_count
        top_canvas.after(100, animate_gif, frame_index)

    animate_gif(0)

    open_icon = ImageTk.PhotoImage(Image.open("image\\open_menu.png").resize((30, 30), Image.Resampling.LANCZOS))
    close_icon = ImageTk.PhotoImage(Image.open("image\\close_menu.png").resize((30, 30), Image.Resampling.LANCZOS))
    light_mode_icon = ImageTk.PhotoImage(
        Image.open("image\\bright_mode.png").resize((35, 35), Image.Resampling.LANCZOS))
    dark_mode_icon = ImageTk.PhotoImage(Image.open("image\\dark_mode.png").resize((35, 35), Image.Resampling.LANCZOS))

    view_stalls_icon = ImageTk.PhotoImage(
        Image.open("image\\apply_stall.png").resize((30, 30), Image.Resampling.LANCZOS))
    assign_stall_icon = ImageTk.PhotoImage(
        Image.open("image\\assign_stall.png").resize((30, 30), Image.Resampling.LANCZOS))
    view_tenants_icon = ImageTk.PhotoImage(
        Image.open("image\\view_tenants.png").resize((30, 30), Image.Resampling.LANCZOS))
    generate_reports_icon = ImageTk.PhotoImage(
        Image.open("image\\reports.png").resize((30, 30), Image.Resampling.LANCZOS))
    notification_icon = ImageTk.PhotoImage(
        Image.open("image\\notification.png").resize((30, 30), Image.Resampling.LANCZOS))
    profile_icon = ImageTk.PhotoImage(Image.open("image\\profiles.png").resize((30, 30), Image.Resampling.LANCZOS))
    auditor_icon = ImageTk.PhotoImage(Image.open("image\\auditor.png").resize((30, 30), Image.Resampling.LANCZOS))

    category_icons = {
        "Manage Stalls": view_stalls_icon,
        "Tenants": view_tenants_icon,
        "Auditor": auditor_icon,
        "Reports": generate_reports_icon,
        "Notification": notification_icon,
        "Profile": profile_icon
    }

    collapsed_icon_frame = Frame(admin_window, bg="#C3C3C3", height=500, width=50)

    title_text_id = top_canvas.create_text(800, 40, text="Admin Dashboard", font=('Algerian', 45, 'bold'),
                                           fill='white')

    selected_category = StringVar(value="Manage Stalls")
    selected_category_text_id = top_canvas.create_text(760, 100, text=selected_category.get(),
                                                       font=('Bauhaus 93', 18, 'bold', 'underline'), fill='#796796')
    top_canvas.itemconfigure(selected_category_text_id, state='hidden')

    profile_image = Image.open("image\\people.png")
    profile_image = profile_image.resize((50, 50), Image.Resampling.LANCZOS)
    mask = Image.new("L", profile_image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((1, 1, 49, 49), fill=255)
    profile_image.putalpha(mask)
    profile_image_tk = ImageTk.PhotoImage(profile_image)
    profile_image_id = top_canvas.create_image(20, 100, image=profile_image_tk, anchor='nw')
    top_canvas.profile_image_tk = profile_image_tk

    username_text_id = top_canvas.create_text(90, 135, text=logged_in_user['username'],
                                              font=('Arial', 16, 'underline', 'bold'), fill='blue', anchor='w')
    top_canvas.tag_bind(username_text_id, "<Button-1>", open_edit_user_info_and_close_dashboard)

    date_time_text_id = top_canvas.create_text(1400, 130, font=('Arial', 12, 'bold'), fill='white')

    def update_time_and_date():
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        day_str = now.strftime("%A")
        formatted_str = f"{date_str}    {time_str}    {day_str}"
        top_canvas.itemconfig(date_time_text_id, text=formatted_str)
        top_canvas.after(1000, update_time_and_date)

    update_time_and_date()

    toggle_theme_btn = Button(admin_window, image=light_mode_icon, command=toggle_theme, bg='black', borderwidth=0)
    top_canvas.toggle_theme_btn_id = top_canvas.create_window(1230, 110, anchor='nw', window=toggle_theme_btn)

    category_frame = Frame(admin_window, bg="#C3C3C3", height=500, width=200)
    category_frame.pack(side='left', fill='y')

    toggle_category_btn = Button(category_frame, image=close_icon, command=toggle_categories, bg='black', borderwidth=0)
    toggle_category_btn.pack(side='top', anchor='w', pady=10, padx=10)

    categories = ["Manage Stalls", "Tenants", "Auditor", "Reports", "Notification", "Profile"]
    category_buttons = []

    for category in categories:
        btn = Button(category_frame, text=category, image=category_icons[category], compound='left',
                     command=lambda c=category: update_selected_category(c),
                     height=35, anchor='w', font=('Arial', 14, 'bold'), fg='black', bg='#919191', borderwidth=0, padx=5)
        btn.pack(side='top', fill='x', padx=10, pady=10)
        category_buttons.append(btn)

    # Load the logout icon
    logout_icon = ImageTk.PhotoImage(Image.open("image\\logout.png").resize((30, 30), Image.Resampling.LANCZOS))

    logout_btn = Button(category_frame, text="Logout", compound='left', image=logout_icon, command=logout,
                        height=35, anchor='w', font=('Arial', 14, 'bold'), fg='black', bg='#919191', borderwidth=0,
                        padx=5)
    logout_btn.pack(side='bottom', fill='x', padx=10, pady=10)

    content_frame = Frame(admin_window, bg="#f8f8f8")
    content_frame.pack(side='right', fill='both', expand=True)

    update_selected_category(selected_category.get())

def tenant_part():
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Frame for assignments
    tenant_part_frame = Frame(content_frame, bg="#EAE8FF", padx=10, pady=10, bd=2, relief='groove')
    tenant_part_frame.pack(fill='both', expand=True, padx=20, pady=20)

    # Title frame for animated welcome message
    title_frame = ctk.CTkFrame(tenant_part_frame, fg_color="white", corner_radius=20)
    title_frame.pack(side="top", fill="x", padx=10, pady=(10, 0))

    title2_label = ctk.CTkLabel(title_frame, text="", font=('Bauhaus 93', 26, 'bold'), text_color='#0016BA')
    title2_label.pack(side='top', pady=10)

    # Define the full text for animation
    full_text = "Tenant Part:"

    def animate_text(index=0):
        if index < len(full_text):
            title2_label.configure(text=full_text[:index + 1])
            title2_label.after(150, animate_text, index + 1)
        else:
            title2_label.after(1000, animate_text, 0)

    animate_text()

    # Load icons for each label
    view_icon = ImageTk.PhotoImage(Image.open("image\\view_tenants.png").resize((50, 50), Image.Resampling.LANCZOS))
    attendance_icon = ImageTk.PhotoImage(Image.open("image\\attendance.png").resize((50, 50), Image.Resampling.LANCZOS))
    assign_stall_icon = ImageTk.PhotoImage(
        Image.open("image\\assign_stall.png").resize((50, 50), Image.Resampling.LANCZOS))
    admin_feedback_icon = ImageTk.PhotoImage(
        Image.open("image\\feedback.png").resize((50, 50), Image.Resampling.LANCZOS))

    # Content Frame with Gradient Background
    info_frame = ctk.CTkFrame(tenant_part_frame, fg_color="white", corner_radius=20)
    info_frame.pack(expand=True, fill="both", pady=20, padx=20)

    # Creating a canvas for gradient background
    gradient_canvas = Canvas(info_frame, width=info_frame.winfo_width(), height=info_frame.winfo_height())
    gradient_canvas.pack(fill="both", expand=True)

    # Function to draw a vertical gradient
    def draw_gradient(canvas, color1, color2):
        width = info_frame.winfo_width()
        height = info_frame.winfo_height()
        steps = 100  # Number of gradient steps

        for i in range(steps):
            r = int(color1[1:3], 16) + (int(color2[1:3], 16) - int(color1[1:3], 16)) * i // steps
            g = int(color1[3:5], 16) + (int(color2[3:5], 16) - int(color1[3:5], 16)) * i // steps
            b = int(color1[5:7], 16) + (int(color2[5:7], 16) - int(color1[5:7], 16)) * i // steps
            color = f'#{r:02x}{g:02x}{b:02x}'
            canvas.create_rectangle(0, i * height // steps, width, (i + 1) * height // steps, outline=color, fill=color)

    # Draw gradient (e.g., light blue to deep blue)
    info_frame.update_idletasks()  # Ensure frame has rendered dimensions
    draw_gradient(gradient_canvas, "#EAE8FF", "#8384C2")

    # Label Frames Section
    label_frame = Frame(info_frame, bg="#f8f8f8")
    label_frame.place(relx=0.5, rely=0.5, anchor="center")

    # Helper function to create hover-effect labels with icons
    def create_hover_label(frame, image, text, command, row, col):
        # Create a small frame for each label with fixed width and height
        label_container = Frame(frame, bg="#f8f8f8", bd=1, relief="solid", padx=10, pady=10, width=200, height=200)
        label_container.grid(row=row, column=col, padx=10, pady=10)
        label_container.pack_propagate(False)  # Prevents resizing based on content

        # Create the label with icon and text inside the small frame
        label = Label(
            label_container, text=text, image=image, compound="top",
            font=("Helvetica", 14), fg="#8384C2", bg="#f8f8f8",  # Set text color
            padx=5, pady=10
        )
        label.image = image  # Keep a reference to avoid garbage collection
        label.pack(expand=True)  # Center the content within the small frame

        # Bind hover effects to underline text on hover and call function on click
        label.bind('<Enter>', lambda event: label.config(font=('Helvetica', 14, 'underline')))
        label.bind('<Leave>', lambda event: label.config(font=('Helvetica', 14)))
        label.bind('<Button-1>', lambda event: command())

    # Creating each label with hover effect and icon-text spacing
    create_hover_label(label_frame, view_icon, "View tenants", view_tenants, row=0, col=0)
    create_hover_label(label_frame, attendance_icon, "View Attendance", view_tenant_attendance, row=0, col=1)
    create_hover_label(label_frame, assign_stall_icon, "Assign Stall", assign_stall, row=0, col=2)
    create_hover_label(label_frame, admin_feedback_icon, "Tenant Feedback", admin_feedback, row=0, col=3)

def auditor_part():
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Frame for assignments
    auditor_part_frame = Frame(content_frame, bg="#EAE8FF", padx=10, pady=10, bd=2, relief='groove')
    auditor_part_frame.pack(fill='both', expand=True, padx=20, pady=20)

    # Title frame for animated welcome message
    title_frame = ctk.CTkFrame(auditor_part_frame, fg_color="white", corner_radius=20)
    title_frame.pack(side="top", fill="x", padx=10, pady=(10, 0))

    title2_label = ctk.CTkLabel(title_frame, text="", font=('Bauhaus 93', 26, 'bold'), text_color='#0016BA')
    title2_label.pack(side='top', pady=10)

    # Define the full text for animation
    full_text = "Auditor Part:"

    def animate_text(index=0):
        if index < len(full_text):
            title2_label.configure(text=full_text[:index + 1])
            title2_label.after(150, animate_text, index + 1)
        else:
            title2_label.after(1000, animate_text, 0)

    animate_text()

    # Load icons for each label
    auditor_icon = ImageTk.PhotoImage(Image.open("image\\registration.png").resize((50, 50), Image.Resampling.LANCZOS))
    assign_auditor_icon = ImageTk.PhotoImage(
        Image.open("image\\assignment.png").resize((50, 50), Image.Resampling.LANCZOS))
    evidence_icon = ImageTk.PhotoImage(Image.open("image\\evidence.png").resize((50, 50), Image.Resampling.LANCZOS))

    # Content Frame with Gradient Background
    info_frame = ctk.CTkFrame(auditor_part_frame, fg_color="white", corner_radius=20)
    info_frame.pack(expand=True, fill="both", pady=20, padx=20)

    # Creating a canvas for gradient background
    gradient_canvas = Canvas(info_frame, width=info_frame.winfo_width(), height=info_frame.winfo_height())
    gradient_canvas.pack(fill="both", expand=True)

    # Function to draw a vertical gradient
    def draw_gradient(canvas, color1, color2):
        width = info_frame.winfo_width()
        height = info_frame.winfo_height()
        steps = 100  # Number of gradient steps

        for i in range(steps):
            r = int(color1[1:3], 16) + (int(color2[1:3], 16) - int(color1[1:3], 16)) * i // steps
            g = int(color1[3:5], 16) + (int(color2[3:5], 16) - int(color1[3:5], 16)) * i // steps
            b = int(color1[5:7], 16) + (int(color2[5:7], 16) - int(color1[5:7], 16)) * i // steps
            color = f'#{r:02x}{g:02x}{b:02x}'
            canvas.create_rectangle(0, i * height // steps, width, (i + 1) * height // steps, outline=color, fill=color)

    # Draw gradient (e.g., light blue to deep blue)
    info_frame.update_idletasks()  # Ensure frame has rendered dimensions
    draw_gradient(gradient_canvas, "#F3E5F5", "#7E57C2")

    # Label Frames Section
    label_frame = Frame(info_frame, bg="#f8f8f8")
    label_frame.place(relx=0.5, rely=0.5, anchor="center")

    # Helper function to create hover-effect labels with icons
    def create_hover_label(frame, image, text, command, row, col):
        # Create a small frame for each label with fixed width and height
        label_container = Frame(frame, bg="#f8f8f8", bd=1, relief="solid", padx=10, pady=10, width=200, height=200)
        label_container.grid(row=row, column=col, padx=10, pady=10)
        label_container.pack_propagate(False)  # Prevents resizing based on content

        # Create the label with icon and text inside the small frame
        label = Label(
            label_container, text=text, image=image, compound="top",
            font=("Helvetica", 14), fg="#8384C2", bg="#f8f8f8",  # Set text color
            padx=5, pady=10
        )
        label.image = image  # Keep a reference to avoid garbage collection
        label.pack(expand=True)  # Center the content within the small frame

        # Bind hover effects to underline text on hover and call function on click
        label.bind('<Enter>', lambda event: label.config(font=('Helvetica', 14, 'underline')))
        label.bind('<Leave>', lambda event: label.config(font=('Helvetica', 14)))
        label.bind('<Button-1>', lambda event: command())

    # Creating each label with hover effect and icon-text spacing
    create_hover_label(label_frame, auditor_icon, "View Auditor", view_auditors, row=0, col=0)
    create_hover_label(label_frame, assign_auditor_icon, "Assign auditor", assign_auditor, row=0, col=1)
    create_hover_label(label_frame, evidence_icon, "View Evidence", view_evidence, row=0, col=2)

def assign_auditor():
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Frame for assignments
    assign_frame = Frame(content_frame, bg="#D9D6FF", padx=10, pady=10, bd=2, relief='groove')
    assign_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Title Label
    title_label = ctk.CTkLabel(assign_frame, text="Assign Auditor", font=("Bauhaus 93", 24, "bold"),
                               text_color="#00527B")
    title_label.pack(pady=(0, 20))

    # Fetch auditors
    cursor.execute("SELECT auditor_id, fullname FROM auditor")
    auditors = cursor.fetchall()

    def refresh_tenant_dropdown():
        # Fetch tenants with incorrect attendance status or unrecognized scan status, including their full names
        cursor.execute(
            """
            SELECT ar.tenant_id, t.fullname, ar.attendance_records_id, ar.attendance_time
            FROM attendance_records ar
            LEFT JOIN tenant t ON ar.tenant_id = t.tenant_id
            LEFT JOIN auditor_assignments aa ON ar.attendance_records_id = aa.attendance_records_id
            WHERE (ar.attendance_status = 'Wrong Location' OR ar.scan_status = 'unrecognized')
              AND aa.attendance_records_id IS NULL
            """
        )
        tenants_with_issue = cursor.fetchall()

        # Update tenant_menu values with the new list
        tenant_menu.configure(
            values=[f"Tenant: {tenant[1]} (Tenant ID: {tenant[0]}, Record ID: {tenant[2]}, Time: {tenant[3]})" for
                    tenant in tenants_with_issue] if tenants_with_issue else ["None"]
        )

    # Auditor Dropdown
    auditor_label = ctk.CTkLabel(assign_frame, text="Select Auditor:", font=("Arial", 16), text_color="#333")
    auditor_label.pack(anchor='w', padx=5)
    auditor_var = ctk.StringVar(assign_frame)
    auditor_menu = ctk.CTkOptionMenu(assign_frame, variable=auditor_var,
                                     values=[f"{aud[1]} (ID: {aud[0]})" for aud in auditors], fg_color="#E8E8EC",
                                     button_color="#A0A1FF", button_hover_color="#9293E8",
                                     text_color="#333333") if auditors else ctk.CTkOptionMenu(assign_frame,
                                                                                              variable=auditor_var,
                                                                                              values=["None"])
    auditor_menu.pack(pady=(0, 10), fill='x')

    # Tenant Dropdown with attendance time
    tenant_label = ctk.CTkLabel(assign_frame, text="Select Tenant with Attendance Issue:", font=("Arial", 16),
                                text_color="#333")
    tenant_label.pack(anchor='w', padx=5, pady=(10, 0))
    tenant_var = ctk.StringVar(assign_frame)
    tenant_menu = ctk.CTkOptionMenu(assign_frame, variable=tenant_var, values=[], fg_color="#E8E8EC",
                                    button_color="#A0A1FF",
                                    button_hover_color="#9293E8", text_color="#333333")
    tenant_menu.pack(pady=(0, 20), fill='x')

    # Initial call to populate tenant_menu values
    refresh_tenant_dropdown()

    # Submit Button
    submit_button = ctk.CTkButton(assign_frame, text="Assign Auditor",
                                  command=lambda: submit_assignment(auditor_var, tenant_var),
                                  font=("Arial", 16, "bold"), fg_color='#00527B', text_color='white', corner_radius=10)
    submit_button.bind("<Enter>", lambda e: submit_button.configure(fg_color="#0070A8"))
    submit_button.bind("<Leave>", lambda e: submit_button.configure(fg_color="#00527B"))
    submit_button.pack(pady=(0, 10))

    assign_frame.pack_propagate(False)

    def ToggleToBack(event=None):
        if assign_frame is not None:
            assign_frame.destroy()
        auditor_part()

    # Back Label
    lbl_back = Label(assign_frame, text="Back", bg="#D9D6FF", fg="#00A4FF", font=('arial', 12))
    lbl_back.bind('<Enter>', lambda event, label=lbl_back: label.config(font=('arial', 12, 'underline')))
    lbl_back.bind('<Leave>', lambda event, label=lbl_back: label.config(font=('arial', 12)))
    lbl_back.pack(pady=10)
    lbl_back.bind('<Button-1>', ToggleToBack)

    def submit_assignment(auditor_var, tenant_var):
        auditor_selection = auditor_var.get()
        tenant_selection = tenant_var.get()

        # Check if both auditor and tenant are selected
        if auditor_selection == "None" or auditor_selection == "" or tenant_selection == "None" or tenant_selection == "":
            messagebox.showwarning("Selection Error", "Please select both an auditor and a tenant.")
        else:
            # Extract IDs from the selected text
            auditor_id = int(auditor_selection.split("ID: ")[1].replace(")", ""))
            tenant_id = int(tenant_selection.split("Tenant ID: ")[1].split(",")[0])
            attendance_record_id = int(tenant_selection.split("Record ID: ")[1].split(",")[0])

            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # Insert assignment record into database
            auditor_assignments = Auditor_assignments(conn, cursor)
            auditor_assignments.insert_assignment(auditor_id, tenant_id, attendance_record_id)

            # Insert notification record for the auditor
            notification_message = f"Dear Auditor,\n\nYou have been assigned a new task to audit tenant {tenant_id}.\n\n\nBest regards,\nGovernment Stall Rental System"
            cursor.execute(
                "INSERT INTO notification (recipient, recipient_id, message, notification_date) VALUES ('auditor', ?, ?, ?)",
                (auditor_id, notification_message, current_time))
            conn.commit()

            # Fetch auditor email for notification
            cursor.execute("SELECT email_address FROM auditor WHERE auditor_id = ?", (auditor_id,))
            auditor_email = cursor.fetchone()[0]

            # Send email notification to auditor
            send_email_notification(auditor_email, notification_message)

            messagebox.showinfo("Success", "Auditor assigned successfully and notification sent.")
            # Refresh the tenant dropdown to remove the assigned tenant
            refresh_tenant_dropdown()
            # Clear selections in the dropdowns
            auditor_var.set("None")
            tenant_var.set("None")

def view_evidence():
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Frame for evidence display
    evidence_frame = Frame(content_frame, bg="#FFFFFF", bd=2, relief='groove')
    evidence_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Center Title Label
    title_label = ctk.CTkLabel(evidence_frame, text="View Evidence", font=("Bauhaus 93", 22, "bold"), text_color="#333")
    title_label.pack(pady=3)

    # Fetch evidence records with tenant details and attendance information
    cursor.execute("""
        SELECT e.evidence_id, e.image_path, e.reason, e.status, t.tenant_id, t.fullname, ar.attendance_records_id, ar.attendance_time
        FROM evidence e
        JOIN auditor_assignments aa ON e.assignment_id = aa.assignment_id
        JOIN tenant t ON aa.tenant_id = t.tenant_id
        JOIN attendance_records ar ON aa.attendance_records_id = ar.attendance_records_id
        WHERE e.status = 'pending'
    """)
    evidence_records = cursor.fetchall()

    # Frame for Evidence ID label and dropdown
    evidence_select_frame = ctk.CTkFrame(evidence_frame, fg_color="#FFFFFF")
    evidence_select_frame.pack(anchor='center', pady=(5, 20))

    # Evidence ID Label
    evidence_label = ctk.CTkLabel(evidence_select_frame, text="Select Evidence ID:", font=("Arial", 14),
                                  text_color="#333")
    evidence_label.pack(side="left", padx=5)

    # Evidence ID Dropdown
    evidence_var = ctk.StringVar(evidence_frame)
    if evidence_records:
        evidence_menu = ctk.CTkOptionMenu(evidence_select_frame, variable=evidence_var,
                                          values=[f"{evidence[0]}" for evidence in evidence_records],
                                          fg_color="#E8E8EC", button_color="#A0A1FF",
                                          button_hover_color="#9293E8", text_color="#333333")
        evidence_var.set("")  # Set default value to an empty string
        evidence_menu.pack(side="left")

        # Function to display evidence details and image
        def display_evidence_details(*args):
            # Clear previous details
            for widget in evidence_frame.winfo_children():
                if isinstance(widget, ctk.CTkFrame) and widget != evidence_select_frame:
                    widget.destroy()  # Clear all widgets except the dropdown frame

            selected_id = evidence_var.get()
            if selected_id:  # Only display if an ID is selected
                for evidence in evidence_records:
                    if str(evidence[0]) == selected_id:
                        evidence_id, image_path, reason, status, tenant_id, tenant_fullname, attendance_records_id, attendance_time = evidence

                        # Frame to center-align both image and details
                        centered_container = ctk.CTkFrame(evidence_frame, fg_color="#FFFFFF", corner_radius=10,
                                                          border_width=2)
                        centered_container.pack(anchor='center', pady=10, padx=20)

                        # Image Frame
                        image_frame = ctk.CTkFrame(centered_container, fg_color="#FFFFFF")
                        image_frame.pack(side='left', padx=10, pady=20)

                        # Display evidence image
                        try:
                            img = Image.open(image_path)
                            img = img.resize((300, 300), Image.Resampling.LANCZOS)  # Resize image as needed
                            img_tk = ImageTk.PhotoImage(img)
                            img_label = Label(image_frame, image=img_tk, text="", bg="#FFFFFF")
                            img_label.image = img_tk  # Keep a reference to avoid garbage collection
                            img_label.pack(anchor='center')
                        except Exception as e:
                            print("Error loading image:", e)

                        # Image label
                        ctk.CTkLabel(image_frame, text="Evidence Image", font=("Arial", 12, "italic"),
                                     text_color="#777", fg_color="#FFFFFF").pack(anchor='center', pady=(5, 10))

                        # Details Frame
                        details_frame = ctk.CTkFrame(centered_container, fg_color="#FFFFFF")
                        details_frame.pack(side='left', padx=10)

                        # Display each detail with different colors side by side
                        details = [
                            ("Evidence ID:", evidence_id, "#174482"),
                            ("Tenant ID:", tenant_id, "#174482"),
                            ("Tenant Fullname:", tenant_fullname, "#174482"),
                            ("Attendance Record ID:", attendance_records_id, "#174482"),
                            ("Attendance Time:", attendance_time, "#174482"),
                            ("Reason:", reason, "#174482"),
                            ("Status:", status, "#174482")
                        ]

                        for label_text, value_text, color in details:
                            detail_frame = ctk.CTkFrame(details_frame, fg_color="#FFFFFF")
                            detail_frame.pack(anchor='w')

                            # Label for the text
                            label = ctk.CTkLabel(detail_frame, text=label_text, font=("Arial", 12, "bold"),
                                                 text_color=color)
                            label.pack(side='left')

                            # Label for the value
                            value = ctk.CTkLabel(detail_frame, text=f"{value_text}", font=("Arial", 12),
                                                 text_color="#333")
                            value.pack(side='left', padx=(5, 0))

                        # Approve and Reject Buttons Frame
                        buttons_frame = ctk.CTkFrame(evidence_frame, fg_color="#FFFFFF")
                        buttons_frame.pack(anchor='center', pady=(10, 10))

                        # Approve Button
                        approve_button = ctk.CTkButton(buttons_frame, text="Approve", fg_color="#4CAF50",
                                                       text_color="white",
                                                       command=lambda ev_id=evidence_id: update_evidence_status(ev_id,
                                                                                                                'approve'))
                        approve_button.bind("<Enter>", lambda e: approve_button.configure(fg_color="#59CC5D"))
                        approve_button.bind("<Leave>", lambda e: approve_button.configure(fg_color="#4CAF50"))
                        approve_button.pack(side='left', padx=(0, 10))  # Add some padding to the right

                        # Reject Button
                        reject_button = ctk.CTkButton(buttons_frame, text="Reject", fg_color="#F44336",
                                                      text_color="white",
                                                      command=lambda ev_id=evidence_id: update_evidence_status(ev_id,
                                                                                                               'reject'))
                        reject_button.bind("<Enter>", lambda e: reject_button.configure(fg_color="#FF7474"))
                        reject_button.bind("<Leave>", lambda e: reject_button.configure(fg_color="#F44336"))
                        reject_button.pack(side='left')

        # Call display function whenever selection changes
        evidence_var.trace("w", display_evidence_details)

    else:
        ctk.CTkLabel(evidence_frame, text="No pending evidence.", font=("Arial", 14), text_color="#333").pack(
            anchor='center', pady=20)

    evidence_frame.pack_propagate(False)

    def ToggleToBack(event=None):
        if evidence_frame is not None:
            evidence_frame.destroy()
        auditor_part()

    # Close button
    close_button = ctk.CTkButton(evidence_frame, text="Close", command=ToggleToBack, fg_color="#174482")
    close_button.bind("<Enter>", lambda e: close_button.configure(fg_color="#1E58A8"))
    close_button.bind("<Leave>", lambda e: close_button.configure(fg_color="#174482"))
    close_button.pack(side='bottom', padx=10, pady=3)

def update_evidence_status(evidence_id, status, distance_meters=10):
    tenant_id = None
    attendance_records_id = None  # Initialize attendance_records_id

    # Step 1: Fetch the assignment_id from the evidence table
    cursor.execute("SELECT assignment_id FROM evidence WHERE evidence_id = ?", (evidence_id,))
    assignment = cursor.fetchone()

    if assignment:
        assignment_id = assignment[0]

        # Get the attendance_records_id and tenant_id from auditor_assignments
        cursor.execute("SELECT attendance_records_id, tenant_id FROM auditor_assignments WHERE assignment_id = ?",
                       (assignment_id,))
        assignment_details = cursor.fetchone()

        if assignment_details:
            attendance_records_id, tenant_id = assignment_details

            # Get the stall_id based on tenant_id from the rental table
            cursor.execute("SELECT stall_id FROM rental WHERE tenant_id = ?", (tenant_id,))
            rental_record = cursor.fetchone()

            if rental_record:
                stall_id = rental_record[0]

                # Step 4: Get latitude and longitude from the stall table
                cursor.execute("SELECT latitude, longitude FROM stall WHERE stall_id = ?", (stall_id,))
                stall_location = cursor.fetchone()

                if stall_location:
                    latitude, longitude = stall_location

                    # Calculate new latitude and longitude based on the distance
                    lat_distance = distance_meters / 111139  # 1 degree of latitude ~111,139 meters
                    long_distance = distance_meters / (111139 * math.cos(math.radians(latitude)))

                    # Adjust latitude and longitude
                    new_latitude = latitude + lat_distance
                    new_longitude = longitude + long_distance

                    # Update attendance_records table with the new values
                    if status == "approve":
                        attendance_status = "Correct Location"
                        scan_status = "recognized"
                    else:
                        attendance_status = "Wrong Location"
                        scan_status = "unrecognized"

                    cursor.execute("""
                        UPDATE attendance_records 
                        SET latitude = ?, longitude = ?, attendance_status = ? , scan_status = ?
                        WHERE attendance_records_id = ?
                    """, (new_latitude, new_longitude, attendance_status, scan_status, attendance_records_id))
                    conn.commit()

    # Update the evidence status
    cursor.execute("UPDATE evidence SET status = ? WHERE evidence_id = ?", (status, evidence_id))
    conn.commit()

    # Fetch attendance_time for the notification and email, if attendance_records_id is defined
    if attendance_records_id is not None:
        cursor.execute("SELECT attendance_time FROM attendance_records WHERE attendance_records_id = ?",
                       (attendance_records_id,))
        attendance_record = cursor.fetchone()

        if attendance_record:
            attendance_time = attendance_record[0]
            # Send notification and email to tenant
            send_evidence_notification_to_tenant(tenant_id, evidence_id, status, attendance_time)
            send_evidence_email_to_tenant(tenant_id, evidence_id, status, attendance_time)

            # Display message box after notification and email
            messagebox.showinfo("Success", "Notification and email sent to tenant successfully.")
        else:
            print("Error: attendance_time not found for the given attendance_records_id.")
    else:
        print("Error: attendance_records_id not available, unable to fetch attendance_time or send notifications.")

    # Show success message
    if status == 'approve':
        messagebox.showinfo("Success", "Evidence approved successfully.")
    else:
        messagebox.showinfo("Success", "Evidence rejected successfully.")

    # Refresh the evidence display
    view_evidence()  # Refresh evidence display

def send_evidence_notification_to_tenant(tenant_id, evidence_id, status, attendance_time):
    # Prepare the notification message with attendance_time
    message = f"Dear Tenant,\n\nYour evidence (ID: {evidence_id}) has been {'approved' if status == 'approve' else 'rejected'}.\nAttendance Time: {attendance_time}\n\nBest regards,\nGovernment Stall Rental System"
    notification_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Insert notification into the database
    cursor.execute("""
        INSERT INTO notification (recipient, recipient_id, message, notification_date) 
        VALUES ('tenant', ?, ?, ?)
    """, (tenant_id, message, notification_date))
    conn.commit()

def send_evidence_email_to_tenant(tenant_id, evidence_id, status, attendance_time):
    # Retrieve tenant's email
    cursor.execute("SELECT email_address FROM tenant WHERE tenant_id = ?", (tenant_id,))
    tenant_email = cursor.fetchone()[0]

    # Email setup
    sender_email = "projectall2.2024@gmail.com"
    sender_password = "xiim atxo oajc mtly"
    subject = "Evidence Status Update"
    body = f"Dear Tenant,\n\nYour evidence (ID: {evidence_id}) has been {'approved' if status == 'approve' else 'rejected'}.\nAttendance Time: {attendance_time}\n\nBest regards,\nGovernment Stall Rental System"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = tenant_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Send the email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, tenant_email, msg.as_string())

def send_email_notification(email, message):
    # Email credentials and setup (update with actual credentials)
    sender_email = "projectall2.2024@gmail.com"
    sender_password = "xiim atxo oajc mtly"
    subject = "New Audit Assignment Notification"

    try:
        # Create email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        # Connect to the server and send the email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, msg.as_string())
        print("Email sent successfully.")

    except Exception as e:
        print(f"Failed to send email: {e}")
        messagebox.showwarning("Email Error", "Failed to send email notification.")


def view_auditors():
    # Clear existing widgets
    for widget in content_frame.winfo_children():
        widget.destroy()

    auditor_frame = Frame(content_frame, bg="#D3CAFF", padx=20, pady=10, bd=2, relief='groove')
    auditor_frame.pack(fill='both', expand=True, padx=10, pady=10)

    Label(auditor_frame, text="List of Auditors", font=("Bauhaus 93", 18, 'bold'), bg="#D3CAFF").pack(pady=10)

    # Create a Treeview widget to display auditor details
    auditor_table = ttk.Treeview(auditor_frame, columns=("ID", "Username", "Full Name", "IC", "Email", "Phone"),
                                 show='headings')
    auditor_table.pack(fill='both', expand=True, pady=10)

    # Define the column headings
    auditor_table.heading("ID", text="Auditor ID", anchor='center')
    auditor_table.heading("Username", text="Username", anchor='center')
    auditor_table.heading("Full Name", text="Full Name", anchor='center')
    auditor_table.heading("IC", text="IC", anchor='center')
    auditor_table.heading("Email", text="Email Address", anchor='center')
    auditor_table.heading("Phone", text="Phone Number", anchor='center')

    # Define the column widths
    auditor_table.column("ID", width=100, anchor='center')
    auditor_table.column("Username", width=150, anchor='center')
    auditor_table.column("Full Name", width=200, anchor='center')
    auditor_table.column("IC", width=150, anchor='center')
    auditor_table.column("Email", width=250, anchor='center')
    auditor_table.column("Phone", width=150, anchor='center')

    try:
        # Query to fetch auditor details
        cursor.execute("""
            SELECT auditor_id, username, fullname, ic, email_address, phone_number 
            FROM auditor
        """)
        auditors = cursor.fetchall()

        if auditors:
            for auditor in auditors:
                auditor_id, username, fullname, ic, email, phone = auditor
                # Insert each auditor's information into the Treeview
                auditor_table.insert("", "end", values=(auditor_id, username, fullname, ic, email, phone))
        else:
            Label(auditor_frame, text="No auditors found.", font=("Arial", 14), bg="#D3CAFF").pack(pady=10)

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error fetching auditor data: {e}")

    def ToggleToBack(event=None):
        if auditor_frame is not None:
            auditor_frame.destroy()
        auditor_part()  # Replace with the function that goes back to the previous view

    # Close map button
    close_button = Label(auditor_frame, text="Close", fg="#00A4FF", font=('arial', 12), bg="#D3CAFF")
    close_button.bind('<Enter>', lambda event, label=close_button: label.config(font=('arial', 12, 'underline')))
    close_button.bind('<Leave>', lambda event, label=close_button: label.config(font=('arial', 12)))
    close_button.bind('<Button-1>', lambda event: ToggleToBack())  # Replace with your actual function
    close_button.pack(side='bottom', padx=10)

    # Function to open a popup window to insert a new IC for an auditor
    def insert_auditor_ic():
        # Create a new popup window
        popup = Toplevel(auditor_frame)
        popup.title("Insert Auditor IC")
        popup.geometry("300x150")
        popup.configure(bg="#D3CAFF")

        Label(popup, text="Enter Auditor IC", font=("Arial", 12, 'bold'), bg="#D3CAFF").pack(pady=10)

        ic_entry = Entry(popup, font=("Arial", 12))
        ic_entry.pack(pady=5)

        def save_ic():
            admin = Admin(conn, cursor)
            tenant = Tenant(conn, cursor)
            auditor = Auditor(conn, cursor)
            ic = ic_entry.get().strip()

            # IC format pattern
            ic_pattern = r"^\d{6}-\d{2}-\d{4}$"
            if not re.match(ic_pattern, ic):
                messagebox.showerror("Error", "IC must be in the format XXXXXX-XX-XXXX (6 digits-2 digits-4 digits)!")
                return

            # Ensure IC is unique across admin, tenant, and auditor tables
            if admin.get_admin_by_ic(ic) or tenant.get_tenant_by_ic(ic) or auditor.get_auditor_by_ic(ic):
                messagebox.showerror("Error", "IC number is already registered!")
                return

            try:
                # Insert the new IC into the auditor table
                cursor.execute("INSERT INTO auditor (ic) VALUES (?)", (ic,))
                conn.commit()
                messagebox.showinfo("Success", "Auditor IC inserted successfully!")
                popup.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to insert IC: {e}")

        # Save button in popup
        save_button = ctk.CTkButton(popup, text="Save", command=save_ic, font=("Arial", 10),
                                    fg_color="#8387CC", text_color="white", hover_color="#7174AF")
        save_button.pack(pady=10)

    # Button to insert a new IC
    insert_ic_button = ttk.Button(auditor_frame, text="Insert New Auditor IC", command=insert_auditor_ic)
    insert_ic_button.pack(side='top', pady=5)


def view_tenants():
    # Clear existing widgets
    for widget in content_frame.winfo_children():
        widget.destroy()

    tenant_frame = Frame(content_frame, bg="#D3CAFF", padx=20, pady=10, bd=2, relief='groove')
    tenant_frame.pack(fill='both', expand=True, padx=10, pady=10)

    Label(tenant_frame, text="List of Tenants", font=("Bauhaus 93", 18, 'bold'), bg="#D3CAFF").pack(pady=10)

    # Create a Treeview widget to display tenant details
    tenant_table = ttk.Treeview(tenant_frame, columns=(
        "ID", "Username", "Full Name", "IC", "Email", "Phone", "Stall ID", "Start Date", "End Date"), show='headings')
    tenant_table.pack(fill='both', expand=True, pady=10)

    # Define the column headings
    tenant_table.heading("ID", text="Tenant ID", anchor='center')
    tenant_table.heading("Username", text="Username", anchor='center')
    tenant_table.heading("Full Name", text="Full Name", anchor='center')
    tenant_table.heading("IC", text="IC", anchor='center')
    tenant_table.heading("Email", text="Email Address", anchor='center')
    tenant_table.heading("Phone", text="Phone Number", anchor='center')
    tenant_table.heading("Stall ID", text="Stall ID", anchor='center')
    tenant_table.heading("Start Date", text="Start Date", anchor='center')
    tenant_table.heading("End Date", text="End Date", anchor='center')

    # Define the column widths
    tenant_table.column("ID", width=100, anchor='center')
    tenant_table.column("Username", width=100, anchor='center')
    tenant_table.column("Full Name", width=200, anchor='center')
    tenant_table.column("IC", width=100, anchor='center')
    tenant_table.column("Email", width=250, anchor='center')
    tenant_table.column("Phone", width=150, anchor='center')
    tenant_table.column("Stall ID", width=100, anchor='center')
    tenant_table.column("Start Date", width=120, anchor='center')
    tenant_table.column("End Date", width=120, anchor='center')

    try:
        # Query to join tenant and rental tables based on tenant_id and include start_date and end_date
        cursor.execute("""
            SELECT tenant.tenant_id, tenant.username, tenant.fullname, tenant.ic, tenant.email_address, tenant.phone_number, 
                   rental.stall_id, rental.start_date, rental.end_date
            FROM tenant
            LEFT JOIN rental ON tenant.tenant_id = rental.tenant_id
        """)
        tenants = cursor.fetchall()

        if tenants:
            for tenant in tenants:
                tenant_id, username, fullname, ic, email, phone, stall_id, start_date, end_date = tenant
                stall_id = stall_id if stall_id is not None else "No Stall"  # Handle case where tenant has no stall assigned
                start_date = start_date if start_date else "N/A"  # Handle None values for dates
                end_date = end_date if end_date else "N/A"
                # Insert each tenant and their associated stall and rental dates into the Treeview
                tenant_table.insert("", "end", values=(
                    tenant_id, username, fullname, ic, email, phone, stall_id, start_date, end_date))
        else:
            Label(tenant_frame, text="No tenants found.", font=("Arial", 14), bg="#D3CAFF").pack(pady=10)

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error fetching tenant data: {e}")

    # Function to open a popup window to insert a new IC for a tenant
    def insert_tenant_ic():
        # Create a new popup window
        popup = Toplevel(tenant_frame)
        popup.title("Insert Tenant IC")
        popup.geometry("300x150")
        popup.configure(bg="#D3CAFF")

        Label(popup, text="Enter Tenant IC", font=("Arial", 12, 'bold'), bg="#D3CAFF").pack(pady=10)

        ic_entry = Entry(popup, font=("Arial", 12))
        ic_entry.pack(pady=5)

        def save_ic():
            admin = Admin(conn, cursor)
            tenant = Tenant(conn, cursor)
            auditor = Auditor(conn, cursor)
            ic = ic_entry.get().strip()

            # IC format pattern
            ic_pattern = r"^\d{6}-\d{2}-\d{4}$"
            if not re.match(ic_pattern, ic):
                messagebox.showerror("Error", "IC must be in the format XXXXXX-XX-XXXX (6 digits-2 digits-4 digits)!")
                return

            # Ensure IC is unique across admin, tenant, and auditor tables
            if admin.get_admin_by_ic(ic) or tenant.get_tenant_by_ic(ic) or auditor.get_auditor_by_ic(ic):
                messagebox.showerror("Error", "IC number is already registered!")
                return

            try:
                # Insert the new IC into the tenant table
                cursor.execute("INSERT INTO tenant (ic) VALUES (?)", (ic,))
                conn.commit()
                messagebox.showinfo("Success", "Tenant IC inserted successfully!")
                popup.destroy()
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to insert IC: {e}")

        # Save button in popup
        save_button = ctk.CTkButton(popup, text="Save", command=save_ic, font=("Arial", 10),
                                    fg_color="#8387CC", text_color="white", hover_color="#7174AF")
        save_button.pack(pady=10)

    # Button to insert a new IC
    insert_ic_button = ttk.Button(tenant_frame, text="Insert New Tenant IC", command=insert_tenant_ic)
    insert_ic_button.pack(side='top', pady=5)

    def ToggleToBack(event=None):
        if tenant_frame is not None:
            tenant_frame.destroy()
        tenant_part()

    # Close map button
    close_button = Label(tenant_frame, text="Close", fg="#00A4FF", font=('arial', 12), bg="#D3CAFF")
    close_button.bind('<Enter>',
                      lambda event, label=close_button: label.config(font=('arial', 12, 'underline')))
    close_button.bind('<Leave>', lambda event, label=close_button: label.config(font=('arial', 12)))
    close_button.bind('<Button-1>', lambda event: ToggleToBack())  # Replace with your actual function
    close_button.pack(side='bottom', padx=10)

def view_tenant_attendance():
    for widget in content_frame.winfo_children():
        widget.destroy()  # Clear the content frame

    attendance_frame = Frame(content_frame, bg="#D3CAFF", padx=20, pady=2, bd=2, relief="groove")
    attendance_frame.pack(fill='both', expand=True, padx=10, pady=10)

    Label(attendance_frame, text="Attendance Record", font=('Bauhaus 93', 18, 'bold'), bg="#D3CAFF").pack()

    Label(attendance_frame, text="Select Date:", bg="#D3CAFF").pack(pady=(10, 0))

    # Calendar for selecting date with DD-MM-YYYY format, default to today's date
    today = datetime.datetime.now()
    date_entry = DateEntry(attendance_frame, date_pattern="dd-MM-yyyy", year=today.year, month=today.month,
                           day=today.day)
    date_entry.pack(pady=(0, 10))

    # Button to fetch and display attendance
    fetch_attendance_button = ttk.Button(attendance_frame, text="Fetch Attendance",
                                         command=lambda: open_map_view(date_entry.get_date(), attendance_frame))
    fetch_attendance_button.pack(pady=(0, 10))

def open_map_view(selected_date, attendance_frame):
    # Check if map_frame already exists and destroy it
    for widget in attendance_frame.winfo_children():
        if isinstance(widget, Frame) and widget['bd'] == 2:  # Check if it's a map_frame
            widget.destroy()

    # Create a new frame for the map and attendance list
    map_frame = Frame(attendance_frame, bg="#D3CAFF", padx=20, pady=10, bd=2, relief='groove')
    map_frame.pack(fill="both", expand=True)

    # Frame for attendance list, displayed on the right side of the map
    attendance_list_frame = Frame(map_frame, bg="#D3CAFF", padx=20, pady=10)
    attendance_list_frame.pack(side="right", fill="y", padx=10)

    # Map widget on the left side
    map_widget = TkinterMapView(map_frame, width=600, height=400, corner_radius=0)
    map_widget.pack(side="top", fill="both", expand=True)

    # Set initial position and zoom for the map (Penang, Malaysia)
    map_widget.set_position(5.4164, 100.3327)
    map_widget.set_zoom(10)

    # Fetch attendance records for the selected date along with tenant names and scan_status
    cursor.execute("""SELECT tenant.tenant_id, tenant.fullname, attendance_records.stall_id, 
                             attendance_records.latitude, attendance_records.longitude, 
                             attendance_records.attendance_status, attendance_records.scan_status
                      FROM attendance_records
                      JOIN tenant ON attendance_records.tenant_id = tenant.tenant_id
                      WHERE DATE(attendance_time) = ?""", (selected_date,))
    attendance_records = cursor.fetchall()

    # Dictionaries to keep track of attendance statuses
    attended_tenants = {}  # Use a dictionary to hold fullname and their status
    for tenant_id, fullname, stall_id, lat, lon, attendance_status, scan_status in attendance_records:
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            print(f"Skipping invalid coordinates for Tenant: {fullname} (Lat: {lat}, Lon: {lon})")
            continue

        marker_text = f"Tenant: {fullname} - Stall ID: {stall_id}"

        # Determine marker color based on attendance status and scan status
        if scan_status == "unrecognized":
            marker_color = "#FADF00"
        else:
            marker_color = "green" if attendance_status == "Correct Location" else "red"

        map_widget.set_marker(lat, lon, text=marker_text, marker_color_circle=marker_color,
                              marker_color_outside=marker_color)
        attended_tenants[fullname] = (attendance_status, scan_status)  # Store fullname with its attendance status

    # Query to get tenants with rentals who have not attended on the selected date
    cursor.execute("""SELECT tenant.tenant_id, tenant.fullname
                      FROM rental
                      JOIN tenant ON rental.tenant_id = tenant.tenant_id
                      WHERE ? BETWEEN rental.start_date AND rental.end_date
                      AND rental.tenant_id NOT IN 
                          (SELECT tenant_id FROM attendance_records WHERE DATE(attendance_time) = ?)""",
                   (selected_date, selected_date))
    not_attended_tenants = [fullname for (_, fullname) in cursor.fetchall()]

    # Attendance list display for tenants who have and haven't attended
    Label(attendance_list_frame, text=f"Attendance Summary for {selected_date.strftime('%d-%m-%Y')}",
          bg="#D3CAFF", font=("Arial", 12, "bold")).pack(pady=5)

    Label(attendance_list_frame, text="Attended:", bg="#D3CAFF", font=("Arial", 10, "underline")).pack(anchor="w")

    for fullname, (status, scan_status) in attended_tenants.items():
        if scan_status == "unrecognized":
            status_text = "Unrecognized Face"
            status_color = "#FADF00"
        else:
            status_text = "Correct Location" if status == "Correct Location" else "Wrong Location"
            status_color = "green" if status == "Correct Location" else "red"

        # Create a frame for tenant name and status side by side
        attendance_item_frame = Frame(attendance_list_frame, bg="#D3CAFF")
        attendance_item_frame.pack(anchor="w", padx=5, pady=2)

        # Label for Tenant Fullname
        Label(attendance_item_frame, text=f"Tenant: {fullname}", fg='darkblue', bg="#D3CAFF").pack(side="left", padx=5)

        # Label for Status
        status_label = Label(attendance_item_frame, text=status_text, bg="#D3CAFF", fg=status_color)
        status_label.pack(side="left", padx=5)

    Label(attendance_list_frame, text="Not Attended:", bg="#D3CAFF", font=("Arial", 10, "underline")).pack(anchor="w",
                                                                                                           pady=(10, 0))
    for fullname in not_attended_tenants:
        Label(attendance_list_frame, text=f"Tenant: {fullname}", fg='blue', bg="#D3CAFF").pack(anchor="w", padx=5)

    # Status labels (displayed at the bottom of attendance_frame)
    status_labels = {
        'Unrecognized Face': ('Unrecognized Face', '#FADF00'),
        'Wrong Location': ('Wrong Location', 'red'),
        'Correct Location': ('Correct Location', 'green')
    }

    status_frame = Frame(map_frame, bg="#D3CAFF")
    status_frame.pack(side='bottom', fill="x", pady=10)

    for status, (text, color) in status_labels.items():
        status_label = Label(status_frame, text=text, bg=color, fg="white", padx=10, pady=5)
        status_label.pack(side="right", padx=5)

    def ToggleToBack(event=None):
        if attendance_frame is not None:
            attendance_frame.destroy()
        tenant_part()

    # Close map button
    close_map_button = ttk.Button(status_frame, text="Close Map", command=lambda: ToggleToBack())
    close_map_button.pack(side='left', padx=10)

def admin_notification():
    """
    Displays notifications for the currently logged-in user. Tenants can view their own notifications,
    while admins can view all notifications. When a row is selected in the Treeview, it shows the message details beside the Treeview.
    """
    # Clear existing widgets
    for widget in content_frame.winfo_children():
        widget.destroy()

    notification_frame = Frame(content_frame, bg="#C7D3FF", padx=20, pady=10, bd=2, relief='groove')
    notification_frame.pack(fill='both', expand=True, padx=10, pady=10)

    ctk.CTkLabel(notification_frame, text="Notifications", font=("Bauhaus 93", 24), fg_color="#C7D3FF").pack(
        pady=10)

    # Create a frame to hold both the Treeview and the message display
    notification_content_frame = ctk.CTkFrame(notification_frame, fg_color="#C7D3FF", width=500, height=300)
    notification_content_frame.pack(fill='both', expand=False)
    notification_content_frame.pack_propagate(False)

    # Create a frame to hold both the Treeview and the scrollbar together
    table_frame = ctk.CTkFrame(notification_content_frame)
    table_frame.pack(side='left', fill='both', expand=True)

    # Create a Treeview widget to display notifications
    notification_table = ttk.Treeview(table_frame, columns=("Date",), show='headings', height=20)
    notification_table.pack(side='left', fill='both', expand=True)

    # Define the column heading and width for the "Date" column
    notification_table.heading("Date", text="Date")
    notification_table.column("Date", width=150)

    # Create a scrollbar for the Treeview and pack it to the right of the Treeview
    scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=notification_table.yview)
    scrollbar.pack(side='right', fill='y')
    notification_table.configure(yscrollcommand=scrollbar.set)

    # Create a Text widget to display the selected message and pack it
    message_display = ctk.CTkTextbox(notification_content_frame, height=20, wrap="word", state="disabled")
    message_display.pack(side='right', fill='both', expand=True, padx=10, pady=10)

    def on_row_select(event):
        selected_item = notification_table.selection()
        if selected_item:
            item_values = notification_table.item(selected_item, 'values')
            notification_id = notification_table.item(selected_item, 'tags')[0]
            if item_values:
                cursor.execute("SELECT message FROM notification WHERE notification_id = ?", (notification_id,))
                message = cursor.fetchone()

                if message:
                    selected_message = message[0]
                    message_display.configure(state="normal")
                    message_display.delete("1.0", END)
                    message_display.insert("1.0", selected_message)
                    message_display.configure(state="disabled")

    notification_table.bind("<<TreeviewSelect>>", on_row_select)

    message_displayed = False
    no_notifications_label = None

    def twinkle_label():
        if no_notifications_label:
            current_color = no_notifications_label.cget("text_color")
            new_color = "#FF0000" if current_color == "#C7D3FF" else "#C7D3FF"
            no_notifications_label.configure(text_color=new_color)
            no_notifications_label.after(500, twinkle_label)

    def load_notifications(show_history=False):
        nonlocal message_displayed, no_notifications_label
        notification_table.delete(*notification_table.get_children())
        message_display.configure(state="normal")
        message_display.delete("1.0", END)
        message_display.configure(state="disabled")

        if no_notifications_label:
            no_notifications_label.destroy()
            no_notifications_label = None

        try:
            username = logged_in_user.get("username")
            cursor.execute("SELECT tenant_id FROM tenant WHERE username = ?", (username,))
            tenant = cursor.fetchone()

            if tenant:
                tenant_id = tenant[0]
                if show_history:
                    cursor.execute(
                        "SELECT notification_id, notification_date FROM notification WHERE recipient = 'tenant' AND recipient_id = ? AND is_read = 1 ORDER BY notification_date DESC",
                        (tenant_id,))
                else:
                    cursor.execute(
                        "SELECT notification_id, notification_date FROM notification WHERE recipient = 'tenant' AND recipient_id = ? AND is_read = 0 ORDER BY notification_date DESC",
                        (tenant_id,))
                notifications = cursor.fetchall()

                if not show_history:
                    cursor.execute(
                        "UPDATE notification SET is_read = 1 WHERE recipient = 'tenant' AND recipient_id = ?",
                        (tenant_id,))
            else:
                cursor.execute("SELECT admin_id FROM admin WHERE username = ?", (username,))
                admin = cursor.fetchone()

                if admin:
                    admin_id = admin[0]
                    if show_history:
                        cursor.execute(
                            "SELECT notification_id, notification_date FROM notification WHERE recipient = 'admin' AND recipient_id = ? AND is_read = 1 ORDER BY notification_date DESC",
                            (admin_id,))
                    else:
                        cursor.execute(
                            "SELECT notification_id, notification_date FROM notification WHERE recipient = 'admin' AND recipient_id = ? AND is_read = 0 ORDER BY notification_date DESC",
                            (admin_id,))
                    notifications = cursor.fetchall()

                    if not show_history:
                        cursor.execute(
                            "UPDATE notification SET is_read = 1 WHERE recipient = 'admin' AND recipient_id = ?",
                            (admin_id,))

                else:
                    ctk.CTkLabel(notification_frame, text="User not found.", font=("Arial", 14),
                                 fg_color="#99ccff").pack(pady=10)
                    return

            conn.commit()
            message_displayed = False

            if notifications:
                for notification_id, notification_date in notifications:
                    notification_table.insert("", "end", values=(notification_date,), tags=(notification_id,))
            else:
                if not message_displayed:
                    no_notifications_label = ctk.CTkLabel(notification_frame, text="No notifications available.",
                                                          font=("Arial", 18), text_color="#FF0000", fg_color="#C7D3FF")
                    no_notifications_label.pack(pady=10)
                    message_displayed = True
                    twinkle_label()

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Error retrieving notifications: {e}")

    show_history_var = ctk.BooleanVar(value=False)
    toggle_button = ctk.CTkCheckBox(notification_frame, text="Show Read Notifications", variable=show_history_var,
                                    font=("Arial", 12),
                                    command=lambda: load_notifications(show_history_var.get()))
    toggle_button.pack(pady=10)

    info_frame = ctk.CTkFrame(notification_frame, fg_color="#C7D3FF")
    info_frame.pack(anchor="center", padx=10)

    send_tenant_notification_button = ctk.CTkButton(info_frame, text="Send to Tenant", font=("Arial", 20, "bold"),
                                                    fg_color='#00527B', text_color='white', corner_radius=50,
                                                    command=send_notification_to_tenant)
    send_tenant_notification_button.bind("<Enter>",
                                         lambda e: send_tenant_notification_button.configure(fg_color="#006EA6"))
    send_tenant_notification_button.bind("<Leave>",
                                         lambda e: send_tenant_notification_button.configure(fg_color="#00527B"))
    send_tenant_notification_button.pack(side='left', pady=10, padx=10)

    lbl_text = ctk.CTkLabel(info_frame, text="or", font=('times new roman', 20), fg_color="#C7D3FF")
    lbl_text.pack(side='left', pady=10, padx=10)

    send_auditor_notification_button = ctk.CTkButton(info_frame, text="Send to Auditor", font=("Arial", 20, "bold"),
                                                     fg_color='#00527B', text_color='white', corner_radius=50,
                                                     command=send_notification_to_auditor)
    send_auditor_notification_button.bind("<Enter>",
                                          lambda e: send_auditor_notification_button.configure(fg_color="#006EA6"))
    send_auditor_notification_button.bind("<Leave>",
                                          lambda e: send_auditor_notification_button.configure(fg_color="#00527B"))
    send_auditor_notification_button.pack(side='left', pady=10, padx=10)

    load_notifications()

def send_notification_to_tenant():
    """
    Opens a new frame to send a notification to a selected tenant.
    """
    # Clear existing widgets
    for widget in content_frame.winfo_children():
        widget.destroy()

    send_notification_frame = Frame(content_frame, bg="#C7D3FF", padx=20, pady=10, bd=2, relief='groove')
    send_notification_frame.pack(fill='both', expand=True, padx=10, pady=10)

    Label(send_notification_frame, text="Send Notification", font=("Bauhaus 93", 20, 'bold'), bg="#C7D3FF").pack(
        pady=10)

    # Dropdown to select tenant
    ctk.CTkLabel(send_notification_frame, text="Select Tenant:", font=('Arial', 14),fg_color="#C7D3FF").pack(pady=5)

    # Fetch tenant usernames for dropdown
    cursor.execute("SELECT username FROM tenant")
    tenants = cursor.fetchall()
    tenant_usernames = [tenant[0] for tenant in tenants]

    # Add 'All Tenants' option
    tenant_usernames.insert(0, "All Tenants")

    selected_tenant = StringVar()
    selected_tenant.set("Select Tenant")  # Default dropdown text
    tenant_dropdown = ctk.CTkOptionMenu(send_notification_frame, variable=selected_tenant, values=tenant_usernames,fg_color="#E8E8EC",
                                        button_color="#A0A1FF",button_hover_color="#9293E8", text_color="#333333")
    tenant_dropdown.pack(pady=10)

    # Text widget for notification message
    ctk.CTkLabel(send_notification_frame, text="Notification Message:", font=('Arial', 14)).pack(pady=5)
    message_entry = ctk.CTkTextbox(send_notification_frame, height=200,width=600, wrap="word")
    message_entry.pack(pady=5)

    def send_message():
        tenant_username = selected_tenant.get()
        notification_message = message_entry.get("1.0", END).strip()

        if tenant_username and notification_message:
            # Get the current time
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if tenant_username == "All Tenants":
                # Fetch all tenant IDs for sending to all tenants
                cursor.execute("SELECT tenant_id FROM tenant")
                tenant_ids = cursor.fetchall()

                if tenant_ids:
                    # Insert notification for each tenant
                    for tenant_id in tenant_ids:
                        cursor.execute("""INSERT INTO notification (recipient, recipient_id, message, notification_date, is_read) 
                                          VALUES (?, ?, ?, ?, ?)""",
                                       ('tenant', tenant_id[0], notification_message, current_time, 0))
                    conn.commit()

                    messagebox.showinfo("Success", "Notification sent to all tenants successfully!")
            else:
                # Fetch the tenant_id based on the selected username
                cursor.execute("SELECT tenant_id FROM tenant WHERE username = ?", (tenant_username,))
                tenant_id = cursor.fetchone()

                if tenant_id:
                    tenant_id = tenant_id[0]  # Get the actual tenant_id value

                    # Insert the notification into the database
                    cursor.execute("""INSERT INTO notification (recipient, recipient_id, message, notification_date, is_read) 
                                      VALUES (?, ?, ?, ?, ?)""",
                                   ('tenant', tenant_id, notification_message, current_time, 0))
                    conn.commit()

                    messagebox.showinfo("Success", "Notification sent successfully!")
                else:
                    messagebox.showwarning("Input Error", "Tenant ID not found.")
        else:
            messagebox.showwarning("Input Error", "Please select a tenant and enter a message.")

        # Clear the inputs after successful submission
        selected_tenant.set("Select Tenant")  # Reset the dropdown
        message_entry.delete("1.0", END)  # Clear the message entry field

    send_button = ctk.CTkButton(send_notification_frame, text="Send Notification", command=send_message,
                                font=("Arial", 20, "bold"), fg_color='#00527B', text_color='white',
                                corner_radius=50)
    send_button.bind("<Enter>", lambda e: send_button.configure(fg_color="#006EA6"))
    send_button.bind("<Leave>", lambda e: send_button.configure(fg_color="#00527B"))
    send_button.pack(pady=10)

    # Back button to return to the notifications screen
    back_button = Label(send_notification_frame, text="Back", fg="#00A4FF", font=('arial', 16), bg="#C7D3FF")
    back_button.bind('<Enter>', lambda event, label=back_button: label.config(font=('arial', 16, 'underline')))
    back_button.bind('<Leave>', lambda event, label=back_button: label.config(font=('arial', 16)))
    back_button.bind('<Button-1>', lambda event: admin_notification())  # Replace with your actual function
    back_button.pack(pady=10)

def send_notification_to_auditor():
    """
    Opens a new frame to send a notification to a selected auditor.
    """
    # Clear existing widgets
    for widget in content_frame.winfo_children():
        widget.destroy()

    send_notification_frame = Frame(content_frame, bg="#C7D3FF", padx=20, pady=10, bd=2, relief='groove')
    send_notification_frame.pack(fill='both', expand=True, padx=10, pady=10)

    Label(send_notification_frame, text="Send Notification to Auditor", font=("Bauhaus 93", 20, 'bold'),
          bg="#C7D3FF").pack(pady=10)

    # Dropdown to select auditor
    ctk.CTkLabel(send_notification_frame, text="Select Auditor:", font=('Arial', 14), fg_color="#C7D3FF").pack(pady=5)

    # Fetch auditor usernames for dropdown
    cursor.execute("SELECT fullname FROM auditor")  # Assuming you want to display auditor full names
    auditors = cursor.fetchall()
    auditor_fullnames = [auditor[0] for auditor in auditors]

    # Add 'All Auditors' option
    auditor_fullnames.insert(0, "All Auditors")

    selected_auditor = StringVar()
    selected_auditor.set("Select Auditor")  # Default dropdown text
    auditor_dropdown = ctk.CTkOptionMenu(send_notification_frame, variable=selected_auditor, values=auditor_fullnames,
                                         fg_color="#E8E8EC", button_color="#A0A1FF",button_hover_color="#9293E8", text_color="#333333")
    auditor_dropdown.pack(pady=10)

    # Text widget for notification message
    ctk.CTkLabel(send_notification_frame, text="Notification Message:", font=('Arial', 14)).pack(pady=5)
    message_entry = ctk.CTkTextbox(send_notification_frame, height=200,width=600, wrap="word")
    message_entry.pack(pady=5)

    def send_message():
        auditor_fullname = selected_auditor.get()
        notification_message = message_entry.get("1.0", END).strip()

        if auditor_fullname and notification_message:
            # Get the current time
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            if auditor_fullname == "All Auditors":
                # Fetch all auditor IDs for sending to all auditors
                cursor.execute("SELECT auditor_id FROM auditor")
                auditor_ids = cursor.fetchall()

                if auditor_ids:
                    # Insert notification for each auditor
                    for auditor_id in auditor_ids:
                        cursor.execute("""INSERT INTO notification (recipient, recipient_id, message, notification_date, is_read) 
                                          VALUES (?, ?, ?, ?, ?)""",
                                       ('auditor', auditor_id[0], notification_message, current_time, 0))
                    conn.commit()

                    messagebox.showinfo("Success", "Notification sent to all auditors successfully!")
            else:
                # Fetch the auditor_id based on the selected fullname
                cursor.execute("SELECT auditor_id FROM auditor WHERE fullname = ?", (auditor_fullname,))
                auditor_id = cursor.fetchone()

                if auditor_id:
                    auditor_id = auditor_id[0]  # Get the actual auditor_id value

                    # Insert the notification into the database
                    cursor.execute("""INSERT INTO notification (recipient, recipient_id, message, notification_date, is_read) 
                                      VALUES (?, ?, ?, ?, ?)""",
                                   ('auditor', auditor_id, notification_message, current_time, 0))
                    conn.commit()

                    messagebox.showinfo("Success", "Notification sent successfully!")
                else:
                    messagebox.showwarning("Input Error", "Auditor ID not found.")
        else:
            messagebox.showwarning("Input Error", "Please select an auditor and enter a message.")

        # Clear the inputs after successful submission
        selected_auditor.set("Select Auditor")  # Reset the dropdown
        message_entry.delete("1.0", END)  # Clear the message entry field

    send_button = ctk.CTkButton(send_notification_frame, text="Send Notification", command=send_message,
                                font=("Arial", 20, "bold"), fg_color='#00527B', text_color='white',
                                corner_radius=50)
    send_button.bind("<Enter>", lambda e: send_button.configure(fg_color="#006EA6"))
    send_button.bind("<Leave>", lambda e: send_button.configure(fg_color="#00527B"))
    send_button.pack(pady=10)

    # Back button to return to the notifications screen
    back_button = Label(send_notification_frame, text="Back", fg="#00A4FF", font=('arial', 16), bg="#C7D3FF")
    back_button.bind('<Enter>', lambda event, label=back_button: label.config(font=('arial', 16, 'underline')))
    back_button.bind('<Leave>', lambda event, label=back_button: label.config(font=('arial', 16)))
    back_button.bind('<Button-1>', lambda event: admin_notification())  # Replace with your actual function
    back_button.pack(pady=10)

def generate_report():
    global pdf_btn
    # Clear existing widgets
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Set a theme and style
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("green")

    # Create a container for the report section
    report_frame = Frame(content_frame, bg="#f0f9e8", bd=2, relief="groove")
    report_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Title label
    ctk.CTkLabel(report_frame, text="Generate Report", font=("Bauhaus 93", 22, "bold")).pack(pady=10)

    # Report options with a function to show/hide year selection based on the selected report type
    report_options = ["Monthly Payment Report", "Annual Payment Report", "Unpaid Tenants Report"]
    selected_option = ctk.StringVar(value=report_options[0])  # Default to the first option

    def on_option_change(*args):
        # Show year dropdown only for Monthly Payment Report
        if selected_option.get() == "Monthly Payment Report":
            year_dropdown.pack(side='right', padx=10)  # Pack to the right of the radio button
        else:
            year_dropdown.pack_forget()  # Hide dropdown for other reports

    selected_option.trace_add("write", on_option_change)

    # Display radio buttons for report selection
    options_frame = Frame(report_frame, bg="#f0f9e8")
    options_frame.pack(fill='x', padx=10)

    for option in report_options:
        ctk.CTkRadioButton(options_frame, text=option, variable=selected_option, value=option,
                           font=ctk.CTkFont(size=16)).pack(side='left', anchor='w', padx=10, pady=10)

    # Year selection dropdown for Monthly Payment Report, hidden by default
    current_year = datetime.datetime.now().year
    years = [str(year) for year in range(current_year, current_year - 10, -1)]  # Last 10 years as example
    year_var = ctk.StringVar(value=str(current_year))
    year_dropdown = ttk.Combobox(options_frame, textvariable=year_var, values=years, state="readonly")
    year_dropdown.pack_forget()  # Initially hidden

    # Generate button with hover effect
    generate_btn = ctk.CTkButton(report_frame, text="Generate", font=ctk.CTkFont(size=16, weight="bold"),
                                 command=lambda: generate_report_action(selected_option.get(), year_var.get()))
    generate_btn.pack(pady=10)

    # PDF Button (Initially hidden, will be shown once report is generated)
    pdf_btn = ctk.CTkButton(report_frame, text="Download as PDF", font=ctk.CTkFont(size=16, weight="bold"),
                            command=lambda: generate_pdf(selected_option.get(), year_var.get()), state="disabled")
    pdf_btn.pack(pady=10)

    # Frame to display the report results
    global report_display_frame
    report_display_frame = ctk.CTkFrame(report_frame, fg_color="#e6ffee", corner_radius=10)
    report_display_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Hide the year dropdown initially
    year_dropdown.pack_forget()

    # Force an initial call to the option change handler to hide the dropdown on load
    on_option_change()

def generate_report_action(report_type, selected_year):
    global report_display_frame
    global report_data, fig

    # Clear previous report data
    for widget in report_display_frame.winfo_children():
        widget.destroy()

    # Create a frame for text and chart display side by side
    text_frame = ctk.CTkFrame(report_display_frame, fg_color="#ffffff", corner_radius=10)
    text_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

    chart_frame = ctk.CTkFrame(report_display_frame, fg_color="#ffffff", corner_radius=10)
    chart_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

    try:
        if report_type == "Monthly Payment Report":
            # Use the selected year in the SQL query
            cursor.execute("""
                SELECT strftime('%Y-%m', payment_date) AS month, SUM(amount) AS total_amount
                FROM payment
                WHERE strftime('%Y', payment_date) = ?
                GROUP BY month
            """, (selected_year,))
            data = cursor.fetchall()

            # Prepare report data for display and chart plotting
            if data:
                months, amounts = zip(*[(row[0], row[1]) for row in data if row[1] is not None])
            else:
                months, amounts = [], []

            if not months:
                report_data = f"No payments recorded in {selected_year}."
                fig = None  # No chart to display
            else:
                report_data = "\n".join(
                    [f"Month: {month}, Total Amount: RM{amount:.2f}" for month, amount in zip(months, amounts)]
                )

                # Define a custom gradient of bright blue colors
                colors = [
                    "#add8e6",  # Light Blue
                    "#87ceeb",  # Sky Blue
                    "#00bfff",  # Deep Sky Blue
                    "#1e90ff",  # Dodger Blue
                    "#4169e1",  # Royal Blue
                    "#4682b4",  # Steel Blue
                    "#5f9ea0",  # Cadet Blue
                    "#6495ed",  # Cornflower Blue
                    "#00ced1",  # Dark Turquoise
                    "#1ca3ec",  # Vivid Bright Blue
                    "#0073e6",  # Bright Blue
                    "#005b99",  # Strong Bright Blue
                ]

                # Repeat colors if there are more months than defined colors
                color_cycle = colors * (len(months) // len(colors) + 1)
                bar_colors = color_cycle[:len(months)]

                # Plotting a bar chart for the monthly report
                fig, ax = plt.subplots(figsize=(4, 3))
                ax.bar(months, amounts, color=bar_colors)
                ax.set_title(f"Monthly Payments ({selected_year})", fontsize=12)
                ax.set_xlabel("Month", fontsize=10)
                ax.set_ylabel("Total Amount (RM)", fontsize=10)
                plt.xticks(rotation=45, fontsize=8)
                plt.yticks(fontsize=8)
                plt.tight_layout()

        elif report_type == "Annual Payment Report":
            cursor.execute("""
                SELECT strftime('%Y', payment_date) AS year, SUM(amount) AS total_amount
                FROM payment
                WHERE payment_date IS NOT NULL  -- Exclude entries with NULL payment_date
                GROUP BY year
            """)
            data = cursor.fetchall()

            # Prepare report data
            if data:
                report_data = "\n".join(
                    [f"Year: {row[0]}, Total Amount: RM{row[1]:.2f}" if row[
                                                                            1] is not None else f"Year: {row[0]}, Total Amount: RM0.00"
                     for row in data]
                )
                years = [row[0] for row in data]
                amounts = [row[1] if row[1] is not None else 0 for row in data]  # Replace None with 0

                # Generating a color list using a colormap
                cmap = plt.get_cmap("tab20")  # Using 'tab20' for diverse colors
                colors = [cmap(i) for i in range(len(amounts))]

                # Plotting a pie chart for the annual report
                fig, ax = plt.subplots(figsize=(6, 4))
                ax.pie(amounts, labels=years, autopct='%1.1f%%', startangle=140, colors=colors)
                ax.set_title("Annual Payments Distribution")
                plt.axis('equal')  # Ensures pie is drawn as a circle
            else:
                report_data = "No payments recorded."
                fig = None  # No chart to display

        elif report_type == "Unpaid Tenants Report":

            # Current date for unpaid period limit
            current_date = datetime.date.today()
            current_date_str = current_date.strftime("%d-%B-%Y")
            current_year_month = current_date.strftime("%B %Y")

            # Query unpaid tenants up to the current month and year
            cursor.execute("""
                SELECT t.fullname, p.tenant_id, p.paid_periods
                FROM payment p
                JOIN tenant t ON p.tenant_id = t.tenant_id
                WHERE p.payment_status = 'unpaid'
            """)
            data = cursor.fetchall()

            # Add title at the top of the report
            report_lines = [f"Unpaid Tenants Report up to {current_date_str}"]

            for row in data:
                fullname, tenant_id, paid_periods = row

                # Extract the start date of the paid period and compare with current month/year
                period_start_date_str = paid_periods.split(" to ")[0]
                period_start_date = datetime.datetime.strptime(period_start_date_str, "%d-%m-%Y").date()

                # Check if the unpaid period is up to the current month and year
                if period_start_date <= current_date:
                    report_lines.append(
                        f"Tenant: {fullname} (ID: {tenant_id}), Unpaid Period: {paid_periods}"
                    )

            if len(report_lines) > 1:
                report_data = "\n".join(report_lines)

            else:
                report_data = "No unpaid tenants up to the current period."

            fig = None  # No chart to display for unpaid tenants

        # Display the report data in a Text widget
        report_text = ctk.CTkTextbox(text_frame, wrap='word', padx=20, pady=20, height=300)
        report_text.pack(fill='both', expand=True)
        report_text.insert('1.0', report_data)
        report_text.configure(state='disabled')

        # Display the chart in the chart_frame
        if fig is not None:
            canvas = FigureCanvasTkAgg(fig, master=chart_frame)  # Embed the chart into Tkinter
            canvas.draw()
            canvas.get_tk_widget().pack(fill='both', expand=True)  # Pack the chart widget
        else:
            # If no chart, show "None" in the chart frame
            no_chart_label = ctk.CTkLabel(chart_frame, text="None", font=ctk.CTkFont(size=16))
            no_chart_label.pack(expand=True)

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error generating report: {e}")
    # Once data is generated, enable the PDF button
    pdf_btn.configure(state="normal")

def generate_pdf(report_type, selected_year):
    # File path for saving the PDF
    pdf_file_path = f"{report_type.replace(' ', '_')}_{selected_year}.pdf"

    # Create a PDF canvas
    c = rl_canvas.Canvas(pdf_file_path, pagesize=A4)  # Use rl_canvas here
    width, height = A4

    # Add title and metadata
    c.setFont("Helvetica-Bold", 20)
    c.drawString(2 * cm, height - 2 * cm, f"{report_type}")
    c.setFont("Helvetica", 12)
    c.drawString(2 * cm, height - 3 * cm, f"Year: {selected_year}")

    # Start position for report data text
    text_y_position = height - 4 * cm
    line_height = 14

    # Insert report data into PDF
    c.setFont("Helvetica", 10)
    text_lines = report_data.splitlines()
    for line in text_lines:
        c.drawString(2 * cm, text_y_position, line)
        text_y_position -= line_height
        if text_y_position < 2 * cm:
            c.showPage()  # Start a new page if we run out of space
            text_y_position = height - 2 * cm

    # Save the chart as an image and add it to the PDF
    if fig is not None:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmpfile:
            fig.savefig(tmpfile.name, format='png')
            chart_img = Image.open(tmpfile.name)

            # Resize chart to fit within PDF page width if necessary
            chart_width, chart_height = chart_img.size
            max_width = width - 4 * cm
            if chart_width > max_width:
                scale = max_width / chart_width
                chart_width = max_width
                chart_height = int(chart_height * scale)
                chart_img = chart_img.resize((int(chart_width), int(chart_height)), Image.Resampling.LANCZOS)

            # Convert the image to RGB mode and save as a temporary file
            chart_img_rgb = chart_img.convert('RGB')
            chart_img_rgb.save(tmpfile.name)

            # Insert chart image into the PDF
            c.drawImage(tmpfile.name, 2 * cm, text_y_position - chart_height - 1 * cm, width=chart_width,
                        height=chart_height)
            chart_img.close()

    # Save the PDF
    c.save()

    # Display a message when PDF is generated
    messagebox.showinfo("Success", f"PDF Report generated successfully: {pdf_file_path}")

    # Open the generated PDF automatically using webbrowser
    try:
        webbrowser.open(pdf_file_path)
    except Exception as e:
        messagebox.showerror("Error", f"Could not open PDF: {e}")


def admin_feedback():
    # Clear the content frame
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Global variable to store the currently selected feedback_id
    selected_feedback_id = None

    def load_feedback():
        # Clear the feedback display frame
        for widget in feedback_display_frame.winfo_children():
            widget.destroy()

        conn = sqlite3.connect("stall_rental_system.db")
        cursor = conn.cursor()

        # Fetch all tenant feedback that hasn’t been responded to yet
        cursor.execute(
            "SELECT feedback_id, tenant_id, feedback, feedback_date FROM feedback WHERE response IS NULL ORDER BY feedback_date DESC")
        feedback_data = cursor.fetchall()

        # Display feedback in a structured format
        for feedback_item in feedback_data:
            feedback_id, tenant_id, feedback_text, feedback_date = feedback_item
            tenant_username = get_tenant_username(tenant_id)

            # Format date in a more readable format
            formatted_date = datetime.datetime.strptime(feedback_date, "%Y-%m-%d %H:%M:%S").strftime(
                "%d %B %Y, %I:%M %p")

            # Create a frame to display each feedback entry
            feedback_frame = Frame(feedback_display_frame, bg="#f9f9f9", padx=10, pady=10, bd=2, relief="groove")
            feedback_frame.pack(fill='x', padx=15, pady=10)  # Pack to expand horizontally

            # Display the fields with labels
            Label(feedback_frame, text=f"Feedback ID: {feedback_id}", font=('Arial', 11, 'bold'), fg="#2C3E50",
                  anchor='w').pack(fill='x')
            Label(feedback_frame, text=f"Tenant: {tenant_username}", font=('Arial', 11), fg="#2C3E50", anchor='w').pack(
                fill='x', pady=2)
            Label(feedback_frame, text=f"Date: {formatted_date}", font=('Arial', 11), fg="#2980B9", anchor='w').pack(
                fill='x', pady=2)
            Label(feedback_frame, text=f"Feedback: {feedback_text}", font=('Arial', 11), fg="#2C3E50", anchor='w',
                  wraplength=1000).pack(fill='x', pady=2)

            # Add a response button for each feedback
            respond_button = ctk.CTkButton(feedback_frame, text="Respond", font=('Arial', 11, 'bold'),
                                           fg_color="#636CAD", text_color="white",
                                           hover_color="#717CC7",
                                           command=lambda fid=feedback_id, ftext=feedback_text, fdate=formatted_date,
                                                          tuname=tenant_username: display_feedback_details(fid, ftext,
                                                                                                           fdate,
                                                                                                           tuname))
            respond_button.pack(pady=5, side='right')

        conn.close()

    def get_tenant_username(tenant_id):
        conn = sqlite3.connect("stall_rental_system.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM tenant WHERE tenant_id = ?", (tenant_id,))
        tenant_username = cursor.fetchone()[0]
        conn.close()
        return tenant_username

    def display_feedback_details(feedback_id, feedback_text, feedback_date, tenant_username):
        nonlocal selected_feedback_id
        # Store the selected feedback_id globally
        selected_feedback_id = feedback_id

        # Clear the feedback detail frame beside the response frame
        for widget in feedback_detail_frame.winfo_children():
            widget.destroy()

        # Display selected feedback details beside the response section
        Label(feedback_detail_frame, text=f"Feedback ID: {feedback_id}", font=('Arial', 12, 'bold'), bg="#D5DBDB").pack(
            pady=5)
        Label(feedback_detail_frame, text=f"Tenant: {tenant_username}", font=('Arial', 12), bg="#D5DBDB").pack(pady=5)
        Label(feedback_detail_frame, text=f"Feedback Date: {feedback_date}", font=('Arial', 12), bg="#D5DBDB").pack(
            pady=5)
        Label(feedback_detail_frame, text=f"Feedback: {feedback_text}", font=('Arial', 12), wraplength=400,
              bg="#D5DBDB").pack(pady=5)

    def submit_feedback_response():
        if selected_feedback_id is None:
            messagebox.showerror("Error", "No feedback selected!")
            return

        admin_response = response_text.get("1.0", END).strip()

        if admin_response == "":
            messagebox.showerror("Error", "Response cannot be empty!")
            return

        # Get the logged-in admin's username from the logged_in_user dictionary
        admin_username = logged_in_user.get('username')

        if not admin_username:
            messagebox.showerror("Error", "Admin username not found!")
            return

        # Retrieve the admin_id based on the username from the admin table
        conn = sqlite3.connect("stall_rental_system.db")
        cursor = conn.cursor()

        cursor.execute("SELECT admin_id FROM admin WHERE username = ?", (admin_username,))
        result = cursor.fetchone()

        if result:
            admin_id = result[0]
        else:
            messagebox.showerror("Error", "Admin ID not found for the given username!")
            conn.close()
            return

        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Save response to the database with admin_id
        cursor.execute("UPDATE feedback SET response = ?, response_date = ?, admin_id = ? WHERE feedback_id = ?",
                       (admin_response, current_time, admin_id, selected_feedback_id))
        conn.commit()
        conn.close()

        # Show success message
        messagebox.showinfo("Success", "Response submitted successfully!")

        # Clear the response text box
        response_text.delete("1.0", END)

        # Clear the feedback detail display
        for widget in feedback_detail_frame.winfo_children():
            widget.destroy()

        # Reload the feedback list to remove the responded feedback
        load_feedback()

    def load_feedback_history():
        # Clear the content frame
        for widget in content_frame.winfo_children():
            widget.destroy()

        # Create a frame for displaying the feedback history
        history_container = Frame(content_frame, bg="#D3CAFF", padx=20, pady=5, bd=2, relief="groove")
        history_container.pack(fill='both', expand=True, padx=10, pady=10)

        title_label = Label(history_container, text="Feedback History", bg="#D3CAFF", font=("Bauhaus 93", 20, "bold"),
                            fg="black")
        title_label.pack(pady=(0, 5), anchor='center')

        # Close button to return to admin_feedback_frame
        close_button = Button(history_container, text="Close", font=('Arial', 12, 'bold'), bg="#C0392B", fg="white",
                              command=admin_feedback)
        close_button.pack(pady=10, side='bottom')

        # Create a Canvas to enable scrolling
        canvas = Canvas(history_container, bg="#ECECEC")
        canvas.pack(side='left', fill='both', expand=True)

        # Add a scrollbar for the history display frame
        history_scrollbar = Scrollbar(history_container, orient="vertical", command=canvas.yview)
        history_scrollbar.pack(side='right', fill='y')

        # Configure the canvas to use the scrollbar
        canvas.configure(yscrollcommand=history_scrollbar.set)

        # Create a frame inside the canvas to hold the history content
        history_display_frame = Frame(canvas, bg="#ECECEC")
        canvas_window = canvas.create_window((0, 0), window=history_display_frame, anchor="nw")

        # Configure the canvas to use the scrollbar with dynamic resizing
        history_display_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind('<Configure>', lambda event: canvas.itemconfig(canvas_window, width=event.width))

        conn = sqlite3.connect("stall_rental_system.db")
        cursor = conn.cursor()

        # Query to fetch feedback with responses from all admins
        cursor.execute("""
            SELECT f.feedback_id, f.tenant_id, f.feedback, f.response, f.feedback_date, f.response_date, a.fullname 
            FROM feedback f 
            JOIN admin a ON f.admin_id = a.admin_id 
            WHERE f.response IS NOT NULL
            ORDER BY f.response_date DESC
        """)
        feedback_history_data = cursor.fetchall()

        # Display each feedback history entry
        for feedback_item in feedback_history_data:
            feedback_id, tenant_id, feedback_text, admin_response, feedback_date, response_date, admin_name = feedback_item
            tenant_username = get_tenant_username(tenant_id)

            # Format dates for display
            formatted_feedback_date = datetime.datetime.strptime(feedback_date, "%Y-%m-%d %H:%M:%S").strftime(
                "%d %B %Y, %I:%M %p")
            formatted_response_date = datetime.datetime.strptime(response_date, "%Y-%m-%d %H:%M:%S").strftime(
                "%d %B %Y, %I:%M %p")

            # Create a frame for each feedback history entry
            history_entry_frame = Frame(history_display_frame, bg="#ffffff", padx=10, pady=10, bd=2, relief="groove")
            history_entry_frame.pack(fill='x', padx=15, pady=10)

            Label(history_entry_frame, text=f"Feedback ID: {feedback_id}", font=('Arial', 11, 'bold'),
                  fg="#2C3E50").pack(anchor='w', fill='x', pady=2)

            Label(history_entry_frame, text=f"Tenant: {tenant_username}", font=('Arial', 11), fg="#2C3E50").pack(
                anchor='w', fill='x', pady=(2, 0))
            Label(history_entry_frame, text=f"Feedback: {feedback_text}", font=('Arial', 10), wraplength=1000,
                  fg="#27AE60").pack(anchor='w', fill='x')
            Label(history_entry_frame, text=f"Feedback Date: {formatted_feedback_date}", font=('Arial', 8),
                  fg="#2980B9").pack(anchor='w', fill='x', pady=(0, 2))

            Label(history_entry_frame, text=f"Admin: {admin_name}", font=('Arial', 11), fg="#2C3E50").pack(anchor='w',
                                                                                                           fill='x',
                                                                                                           pady=(2, 0))
            Label(history_entry_frame, text=f"Response: {admin_response}", font=('Arial', 10), wraplength=1000,
                  fg="#27AE60").pack(anchor='w', fill='x')
            Label(history_entry_frame, text=f"Response Date: {formatted_response_date}", font=('Arial', 8),
                  fg="#2980B9").pack(anchor='w', fill='x', pady=(0, 2))

        conn.close()

    admin_feedback_frame = Frame(content_frame, bg="#D3CAFF", padx=20, pady=5, bd=2, relief='groove')
    admin_feedback_frame.pack(fill='both', expand=True, padx=10, pady=10)

    title_label = Label(admin_feedback_frame, text="User Feedback", bg="#D3CAFF", font=("Bauhaus 93", 20, "bold"),
                        fg="black")
    title_label.pack(pady=(0, 5), anchor='center')

    # Create a frame for feedback display (scrollable) at the top
    feedback_container = Frame(admin_feedback_frame, bg="#ECECEC", padx=20, pady=10, bd=2, relief='groove')
    feedback_container.pack(fill='both', expand=True, side='top')

    # Create a Canvas to enable scrolling of the feedback display frame
    canvas = Canvas(feedback_container, bg="#ECECEC")
    canvas.pack(side='left', fill='both', expand=True)

    # Add a scrollbar directly to the feedback display frame
    feedback_scrollbar = Scrollbar(feedback_container, orient="vertical", command=canvas.yview)
    feedback_scrollbar.pack(side='right', fill='y')

    canvas.configure(yscrollcommand=feedback_scrollbar.set)

    # Create a frame inside the canvas to hold the feedback content
    feedback_display_frame = Frame(canvas, bg="#ECECEC")
    canvas_window = canvas.create_window((0, 0), window=feedback_display_frame, anchor="nw")

    # Configure the canvas to use the scrollbar
    feedback_display_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind('<Configure>', lambda event: canvas.itemconfig(canvas_window, width=event.width))

    # Create a frame for both feedback details and admin response side by side
    bottom_frame = Frame(admin_feedback_frame, bg="#D5DBDB", bd=2, relief='groove')
    bottom_frame.pack(fill='x', side='bottom')

    # Frame to display selected feedback details
    feedback_detail_frame = Frame(bottom_frame, bg="#D5DBDB", bd=2, relief='groove')
    feedback_detail_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

    # Frame for admin response
    response_display_frame = Frame(bottom_frame, bg="#D5DBDB", bd=2, relief='groove')
    response_display_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

    response_label = Label(response_display_frame, text="Admin Response:", font=('Algerian', 14, 'bold'), fg="#34495E",
                           bg="#D5DBDB")
    response_label.pack(pady=5)

    response_text = Text(response_display_frame, height=5, width=40, font=('Arial', 12))
    response_text.pack(pady=5)

    # Add a submit button to finalize the response
    submit_button = ctk.CTkButton(response_display_frame, text="Submit Response", font=('Arial', 12, 'bold'),
                                  fg_color="#636CAD", text_color="white", command=submit_feedback_response,
                                  hover_color="#717CC7")
    submit_button.pack(pady=5)

    def ToggleToFeedbackHistory(event=None):  # switching from register to login page.
        if admin_feedback_frame is not None:
            admin_feedback_frame.destroy()
        load_feedback_history()

    history_button = Label(response_display_frame, text="View Feedback History", fg="#00A4FF", font=('Arial', 12),
                           bg="#D5DBDB")
    history_button.bind('<Enter>', lambda event, label=history_button: label.config(font=('arial', 12, 'underline')))
    history_button.bind('<Leave>', lambda event, label=history_button: label.config(font=('arial', 12)))
    history_button.bind('<Button-1>', ToggleToFeedbackHistory)
    history_button.pack(pady=5)

    def ToggleToBack(event=None):
        if admin_feedback_frame is not None:
            admin_feedback_frame.destroy()
        tenant_part()

    # Close map button
    lbl_back = Label(response_display_frame, text="Back", fg="darkblue", bg="#D5DBDB", font=('arial', 12))
    lbl_back.bind('<Enter>', lambda event, label=lbl_back: label.config(font=('arial', 12, 'underline')))
    lbl_back.bind('<Leave>', lambda event, label=lbl_back: label.config(font=('arial', 12)))
    lbl_back.pack(side='bottom')
    lbl_back.bind('<Button-1>', ToggleToBack)

    # Load feedback into the structured display
    load_feedback()

def assign_stall():
    # Clear the content frame
    for widget in content_frame.winfo_children():
        widget.destroy()

    # Create the main display frame with padding and rounded corners
    assign_stall_display_frame = Frame(content_frame, bg="#F4F4F9", bd=2, relief='groove')
    assign_stall_display_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Title Label with custom fonts and center alignment
    title_label = ctk.CTkLabel(assign_stall_display_frame, text="Assign Stall", font=("Bauhaus 93", 26, "bold"),
                               text_color="#333333")
    title_label.pack(pady=10)

    # Select Application Label
    select_application_label = ctk.CTkLabel(assign_stall_display_frame, text="Select Application",
                                            font=("Helvetica", 16, "bold"), text_color="#666666")
    select_application_label.pack(pady=(10, 5))

    # OptionMenu for selecting applications with wider dimensions and modern colors
    application_var = ctk.StringVar(assign_stall_display_frame)
    application_var.set("Choose Application")
    application_menu = ctk.CTkOptionMenu(assign_stall_display_frame, variable=application_var, values=[""], width=300,
                                         height=40, fg_color="#E8E8EC", button_color="#A0A1FF",
                                         button_hover_color="#9293E8", text_color="#333333")
    application_menu.pack(pady=(0, 10))

    # Frame for displaying application information with border and rounded corners
    application_info_frame = ctk.CTkFrame(assign_stall_display_frame, fg_color="#FFFFFF", corner_radius=15,
                                          border_width=2, border_color="#D1D1D6")
    application_info_frame.pack(pady=(20, 10), fill='x', padx=20)

    # Label to display application details
    application_info_label = ctk.CTkLabel(application_info_frame, text="", font=("Helvetica", 14), text_color="#444444")
    application_info_label.pack(pady=20, padx=20)

    # Function to update application options
    def update_application_options(initial_load=False):
        try:
            cursor.execute(
                "SELECT application_id, tenant_id, stall_id, reason, start_date, duration, status FROM applications WHERE status = 'pending'")
            applications = cursor.fetchall()

            if applications:
                application_menu.configure(values=[f"Application ID: {application[0]}" for application in applications])
            else:
                if initial_load:  # Only show the messagebox on initial load
                    messagebox.showinfo("No Applications", "There are no pending applications at the moment.")
                application_menu.configure(values=["No pending applications"])

        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred while fetching applications: {str(e)}")

    update_application_options(initial_load=True)  # Initial load of options

    # Function to display application information
    def display_application_info(application):
        application_id, tenant_id, stall_id, reason, start_date, duration, status = application

        # Query to get the tenant's full name
        cursor.execute("SELECT fullname FROM tenant WHERE tenant_id = ?", (tenant_id,))
        tenant_fullname = cursor.fetchone()
        tenant_fullname = tenant_fullname[0] if tenant_fullname else "Unknown"

        # Clear previous application info
        for widget in application_info_frame.winfo_children():
            widget.destroy()

        # Create a frame to display the application details neatly
        details_frame = ctk.CTkFrame(application_info_frame, fg_color="#FFFFFF", corner_radius=10)
        details_frame.pack(pady=10, padx=20, fill='x')

        # Function to create a row with bold title and normal value
        def create_info_row(frame, title, value):
            row_frame = ctk.CTkFrame(frame, fg_color="#FFFFFF")
            row_frame.pack(fill='x', pady=5)

            title_label = ctk.CTkLabel(row_frame, text=title, font=("Helvetica", 14, "bold"), text_color="#333333")
            title_label.pack(side="left", padx=10)

            value_label = ctk.CTkLabel(row_frame, text=value, font=("Helvetica", 14), text_color="#666666")
            value_label.pack(side="left", padx=10)

        # Add application information in rows
        create_info_row(details_frame, "Application ID:", application_id)
        create_info_row(details_frame, "Tenant ID:", tenant_id)
        create_info_row(details_frame, "Tenant Full Name:", tenant_fullname)
        create_info_row(details_frame, "Stall ID:", stall_id)
        create_info_row(details_frame, "Reason:", reason)
        create_info_row(details_frame, "Start Date:", start_date)
        create_info_row(details_frame, "Duration:", f"{duration} Month(s)")
        create_info_row(details_frame, "Status:", status)

        # Approve and Reject buttons with larger sizes
        approve_button = ctk.CTkButton(details_frame, text="Approve",
                                       command=lambda: process_application(application_id, tenant_id, stall_id,
                                                                           start_date, duration, "approved"),
                                       fg_color="#4CAF50", hover_color="#388E3C", text_color="white", width=150)
        approve_button.pack(pady=(10, 5))

        reject_button = ctk.CTkButton(details_frame, text="Reject",
                                      command=lambda: process_application(application_id, tenant_id, stall_id,
                                                                          start_date, duration, "rejected"),
                                      fg_color="#f44336", hover_color="#d32f2f", text_color="white", width=150)
        reject_button.pack(pady=5)

    # Function to handle application selection
    def on_application_select(selection):
        try:
            cursor.execute(
                "SELECT application_id, tenant_id, stall_id, reason, start_date, duration, status FROM applications WHERE status = 'pending'")
            applications = cursor.fetchall()
            filtered_applications = [application for application in applications if
                                     f"Application ID: {application[0]}" == selection]

            if filtered_applications:
                display_application_info(filtered_applications[0])
            else:
                messagebox.showerror("Error", "No matching application found. Please try again.")
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred while fetching the application: {str(e)}")

    application_menu.configure(command=on_application_select)

    # Function to process application approval/rejection
    def send_email(to_email, subject, message):
        from_email = "projectall2.2024@gmail.com"
        from_password = "xiim atxo oajc mtly"  # Use App Password for Gmail
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        try:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))

            # Create the server connection
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Upgrade the connection to TLS
            server.login(from_email, from_password)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            messagebox.showerror("Email Error", f"Failed to send email: {str(e)}")

    def send_notification(tenant_id, message):
        try:
            # Get the tenant's email address
            cursor.execute("SELECT email_address FROM tenant WHERE tenant_id = ?", (tenant_id,))
            tenant_email = cursor.fetchone()

            if tenant_email:
                tenant_email = tenant_email[0]

                current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                # Insert notification into the database
                cursor.execute(
                    "INSERT INTO notification (recipient, recipient_id, message, notification_date) VALUES (?, ?, ?, ?)",
                    ("tenant", tenant_id, message, current_time)
                )
                conn.commit()

                # Send email notification
                send_email(tenant_email, "Application Status Update", message)
            else:
                messagebox.showwarning("Warning", "Tenant email not found.")
        except Exception as e:
            messagebox.showerror("Database Error", f"Error sending notification: {str(e)}")

    def process_application(application_id, tenant_id, stall_id, start_date, duration, decision):
        if decision == "approved":
            try:
                # Parse start date
                start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()

                # Add the duration in months to get the end date
                end_date_obj = start_date_obj + relativedelta(months=int(duration))
                end_date = end_date_obj.strftime('%Y-%m-%d')

                # Insert into rental table
                cursor.execute(
                    "INSERT INTO rental (tenant_id, stall_id, start_date, end_date) VALUES (?, ?, ?, ?)",
                    (tenant_id, stall_id, start_date, end_date)
                )

                # Get the last inserted rental_id
                rental_id = cursor.lastrowid

                # Generate payment periods and insert into payment table
                current_start_date = start_date_obj
                payment_periods = []
                while current_start_date < end_date_obj:
                    next_period_date = current_start_date + relativedelta(months=1)
                    if next_period_date > end_date_obj:
                        next_period_date = end_date_obj
                    period_label = f"{current_start_date.strftime('%d-%m-%Y')} to {next_period_date.strftime('%d-%m-%Y')}"

                    # Add payment record to payment table
                    cursor.execute(
                        "INSERT INTO payment (tenant_id, rental_id, paid_periods, payment_date, amount, payment_status) "
                        "VALUES (?, ?, ?, ?, ?, ?)",
                        (tenant_id, rental_id, period_label, None, None, 'unpaid')
                    )

                    payment_periods.append((period_label, current_start_date, next_period_date))
                    current_start_date = next_period_date  # Move to the next period

                # Update application status to approved
                applications = Applications(conn, cursor)
                applications.approve_application(application_id)

                # Send notification and email to tenant
                send_notification(tenant_id,
                                  f"Dear Tenant,\n\nYour application for stall ID {stall_id} has been approved. Your rental period starts on {start_date} and ends on {end_date}.\n\n\nBest regards,\nGovernment Stall Rental System")

                messagebox.showinfo("Success",
                                    "Application approved, stall assigned, and payment periods created successfully!")

                # Refresh the assign_stall window after approval
                content_frame.after(0, assign_stall)

            except Exception as e:
                messagebox.showerror("Error", f"Error processing application: {str(e)}")

        else:
            try:
                # Update application status to rejected
                applications = Applications(conn, cursor)
                applications.reject_application(application_id)

                # Send notification and email to tenant
                send_notification(tenant_id,
                                  f"Dear Tenant,\n\nYour application for stall ID {stall_id} has been rejected.\n\n\nBest regards,\nGovernment Stall Rental System")

                messagebox.showinfo("Success", "Application rejected successfully!")

                # Refresh the assign_stall window after rejection
                content_frame.after(0, assign_stall)

            except Exception as e:
                messagebox.showerror("Error", f"Error processing rejection: {str(e)}")

    # Refresh the application list initially
    update_application_options()

    def ToggleToBack(event=None):
        if assign_stall_display_frame is not None:
            assign_stall_display_frame.destroy()
        tenant_part()

    # Close map button
    close_map_button = ttk.Button(assign_stall_display_frame, text="Close", command=lambda: ToggleToBack())
    close_map_button.pack(side='bottom', pady=2)


delete_mode = False  # To track whether delete mode is active
# need just enter number for search
def stalls_admin():
    def toggle_delete_mode():
        global delete_mode
        delete_mode = not delete_mode  # Toggle the delete mode
        refresh_stalls()

    def search_stalls():
        search_term = search_entry.get().strip()
        for widget in scrollable_frame.winfo_children():
            widget.destroy()

        if search_term.isdigit():
            cursor.execute(
                "SELECT stall_id, location, size, rent_price_per_month, latitude, longitude, stall_image "
                "FROM stall WHERE stall_id = ?",
                (search_term,)
            )
        else:
            cursor.execute(
                "SELECT stall_id, location, size, rent_price_per_month, latitude, longitude, stall_image "
                "FROM stall"
            )

        search_results = cursor.fetchall()
        if search_results:
            display_stalls(search_results)
        else:
            ctk.CTkLabel(scrollable_frame, text="No stalls found", fg_color="#C0C0C0", font=("Arial", 14)).pack(pady=10)

    def delete_stall(stall_id):
        cursor.execute("SELECT * FROM rental WHERE stall_id = ?", (stall_id,))
        rental_exists = cursor.fetchone()

        if rental_exists:
            messagebox.showerror("Error", "Stall cannot be deleted as it is currently rented.")
        else:
            delete_stall = Stall(conn, cursor)
            delete_stall.delete_stall(stall_id)

            messagebox.showinfo("Success", "Stall deleted successfully.")
            refresh_stalls()  # Refresh the stall list after deletion

    def refresh_stalls():
        cursor.execute(
            "SELECT stall_id, location, size, rent_price_per_month, latitude, longitude, stall_image FROM stall")
        stalls = cursor.fetchall()
        display_stalls(stalls)

    def display_stalls(stalls):
        for widget in scrollable_frame.winfo_children():
            widget.destroy()  # Clear previous stall displays

        for stall in stalls:
            stall_id, location, size, rent_price_per_month, latitude, longitude, stall_image = stall

            stall_frame = ctk.CTkFrame(scrollable_frame, fg_color="white", border_width=2, border_color='gray')
            stall_frame.pack(fill='x', padx=5, pady=5)  # Use padx and pady here

            if stall_image:
                img = Image.open(stall_image)
                img = img.resize((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                image_label = Label(stall_frame, image=photo, bg="white")
                image_label.image = photo  # Keep a reference to avoid garbage collection
                image_label.pack(side='left', padx=5, pady=5)

            info_frame = ctk.CTkFrame(stall_frame, fg_color="white")
            info_frame.pack(side='left', padx=10)

            ctk.CTkLabel(info_frame, text=f"Stall ID: {stall_id}", fg_color="white", font=("Arial", 12, "bold")).pack(
                anchor='w')
            ctk.CTkLabel(info_frame, text=f"Size: {size}", fg_color="white", font=("Arial", 12, "bold")).pack(
                anchor='w')
            ctk.CTkLabel(info_frame, text=f"Rent: RM{rent_price_per_month}", fg_color="white",
                         font=("Arial", 12, "bold")).pack(anchor='w')

            # Conditionally display delete button if delete mode is active
            if delete_mode:
                delete_icon = ctk.CTkButton(stall_frame, text="❌", command=lambda s_id=stall_id: delete_stall(s_id),
                                            fg_color="#F26163", text_color="white", hover_color="#E65C5E")
                delete_icon.pack(side='right', padx=10)

            edit_icon = ctk.CTkButton(stall_frame, text="Edit", command=lambda sl=stall: edit_stall(sl),
                                      fg_color="#FFD134", text_color="white", hover_color="#F2C731")
            edit_icon.pack(side='right', padx=10)

            info_icon = ctk.CTkButton(stall_frame, text="Info", command=lambda s_id=stall_id: show_stall_info(s_id),
                                      fg_color="#2196F3", text_color="white", hover_color="#186EB3")
            info_icon.pack(side='right', padx=10)

    def fetch_stalls():
        conn = sqlite3.connect("stall_rental_system.db")
        cursor = conn.cursor()

        # Query to get stall statuses based on the rental and applications tables
        cursor.execute("""
            SELECT s.stall_id, s.latitude, s.longitude, 
                   CASE 
                       -- Stall is occupied (exists in the rental table)
                       WHEN r.rental_id IS NOT NULL THEN 'occupied' 
                       -- Stall has a pending application
                       WHEN a.application_id IS NOT NULL AND a.status = 'pending' THEN 'pending' 
                       -- Stall is neither rented nor has a pending application
                       ELSE 'available' 
                   END AS status
            FROM stall s
            -- Left join with rental to check if the stall is rented
            LEFT JOIN rental r ON s.stall_id = r.stall_id
            -- Left join with applications to check if the stall has a pending application
            LEFT JOIN applications a ON s.stall_id = a.stall_id AND a.status = 'pending'
        """)

        # Fetch all results
        stalls = cursor.fetchall()
        conn.close()
        return stalls

    def open_map_view():
        for widget in content_frame.winfo_children():
            widget.destroy()  # Clear the content frame before displaying the map

        map_frame = Frame(content_frame, bg="#D3CAFF", padx=20, pady=10, relief='groove')
        map_frame.pack(fill="both", expand=True, padx=10, pady=10)

        map_widget = TkinterMapView(map_frame, width=600, height=400, corner_radius=0)
        map_widget.pack(fill="both", expand=True)

        # Set initial position and zoom for the map (Penang, Malaysia)
        map_widget.set_position(5.4164, 100.3327)
        map_widget.set_zoom(10)

        # Fetch stalls and add markers based on their status
        stalls = fetch_stalls()

        for stall_id, lat, lon, status in stalls:
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                print(f"Skipping invalid coordinates for Stall ID: {stall_id} (Lat: {lat}, Lon: {lon})")
                continue

            marker_text = f"Stall ID: {stall_id}"

            if status == 'occupied':
                marker_color = "red"
            elif status == 'pending':
                marker_color = "#FADF00"
            else:
                marker_color = "green"

            map_widget.set_marker(lat, lon, text=marker_text, marker_color_circle=marker_color,
                                  marker_color_outside=marker_color)

        bottom_frame = ctk.CTkFrame(map_frame)
        bottom_frame.pack(pady=10, fill='x')

        # Status display labels
        status_frame = Frame(bottom_frame)
        status_frame.pack(anchor='e', pady=5, padx=(30, 10))

        status_labels = {
            'occupied': ('Occupied', 'red'),
            'pending': ('Pending', '#FADF00'),
            'available': ('Available', 'green')
        }

        for status, (text, color) in status_labels.items():
            status_label = Label(status_frame, text=text, bg=color, fg="white", padx=10, pady=5)
            status_label.pack(side="right", padx=5)

        # Close button
        close_map_button = ctk.CTkButton(bottom_frame, text="Close Map", command=stalls_admin, fg_color="#F06062",
                                         text_color="white")
        close_map_button.bind("<Enter>", lambda e: close_map_button.configure(fg_color="#FF6669"))
        close_map_button.bind("<Leave>", lambda e: close_map_button.configure(fg_color="#F06062"))
        close_map_button.pack(anchor='center', pady=5, padx=10)

    for widget in content_frame.winfo_children():
        widget.destroy()

    stall_display_frame = Frame(content_frame, bg="#D3CAFF", padx=20, pady=10, bd=2, relief="groove")
    stall_display_frame.pack(fill='both', expand=True, padx=10, pady=10)

    ctk.CTkLabel(stall_display_frame, text="Manage Stalls", font=("Bauhaus 93", 24), fg_color="#D3CAFF").pack(pady=10)

    global search_entry
    # Create a container frame to hold search and buttons
    search_button_frame = ctk.CTkFrame(stall_display_frame, fg_color="#D3CAFF")
    search_button_frame.pack(fill='x', pady=5)

    # Left-side frame for search bar (center-aligned within search_button_frame)
    search_frame = ctk.CTkFrame(search_button_frame, fg_color="#D3CAFF")
    search_frame.pack(side="top", pady=5)

    # Center the search bar by adding 'expand=True' and 'anchor'
    search_entry = ctk.CTkEntry(search_frame, font=("Arial", 12), width=200, placeholder_text="Enter Stall ID")
    search_entry.pack(side='left', padx=(0, 10), anchor='center')

    search_button = ctk.CTkButton(search_frame, text="Search", command=search_stalls, fg_color="#2196F3",
                                  text_color="white")
    search_button.bind("<Enter>", lambda e: search_button.configure(fg_color="#239DFF"))
    search_button.bind("<Leave>", lambda e: search_button.configure(fg_color="#2196F3"))
    search_button.pack(side='left')

    # Right-side frame for buttons (aligned to the right)
    buttons_frame = ctk.CTkFrame(search_button_frame, fg_color="#D3CAFF")
    buttons_frame.pack(side='right', padx=10)

    location_icon = ctk.CTkImage(Image.open("image\\location.png").resize((40, 40), Image.Resampling.LANCZOS))

    map_button = ctk.CTkButton(buttons_frame, image=location_icon, text="", command=open_map_view,
                               font=("Arial", 12, "bold"),
                               fg_color="#A8E5E0", text_color="white", width=10)
    map_button.bind("<Enter>", lambda e: map_button.configure(fg_color="#B2F2EC"))
    map_button.bind("<Leave>", lambda e: map_button.configure(fg_color="#A8E5E0"))
    map_button.pack(side='right', padx=(10, 0))

    # Add "Add New Stall" and "Delete" buttons to buttons_frame
    toggle_delete_button = ctk.CTkButton(buttons_frame, text="Delete", command=toggle_delete_mode, font=("Arial", 12),
                                         fg_color="#E87F7A", text_color="white")
    toggle_delete_button.bind("<Enter>", lambda e: toggle_delete_button.configure(fg_color="#F59391"))
    toggle_delete_button.bind("<Leave>", lambda e: toggle_delete_button.configure(fg_color="#E87F7A"))
    toggle_delete_button.pack(side='right', padx=(10, 0))

    add_new_stall = ctk.CTkButton(buttons_frame, text="Add New Stall", command=add_stall, font=("Arial", 12, "bold"),
                                  fg_color="#7ECC77", text_color="white")
    add_new_stall.bind("<Enter>", lambda e: add_new_stall.configure(fg_color="#95E08F"))
    add_new_stall.bind("<Leave>", lambda e: add_new_stall.configure(fg_color="#7ECC77"))
    add_new_stall.pack(side='right', padx=(10, 0))

    # Create canvas and scrollbar for the scrollable area
    canvas = Canvas(stall_display_frame, bg="#C0C0C0")
    canvas.pack(side="left", fill="both", expand=True)

    scroll_y = Scrollbar(stall_display_frame, orient="vertical", command=canvas.yview)
    scroll_y.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scroll_y.set)

    scrollable_frame = Frame(canvas, bg="#C0C0C0")
    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind('<Configure>', lambda event: canvas.itemconfig(canvas_window, width=event.width))

    # Fetch and display stalls
    cursor.execute("SELECT stall_id, location, size, rent_price_per_month, latitude, longitude, stall_image FROM stall")
    stalls = cursor.fetchall()
    display_stalls(stalls)


def show_stall_info(stall_id):
    # Create a new window for displaying stall information
    info_window = Toplevel(content_frame)
    info_window.title(f"Stall Information - ID: {stall_id}")
    info_window.geometry("1920x1080+0+0")
    info_window.state("zoomed")
    info_window.configure(bg="#D3CAFF")

    # Fetch stall information from the database
    cursor.execute(
        "SELECT stall_image, location, size, rent_price_per_month, latitude, longitude FROM stall WHERE stall_id = ?",
        (stall_id,),
    )
    stall_info = cursor.fetchone()

    if stall_info:
        stall_image_path, location, size, rent_price, latitude, longitude = stall_info

        # Create a frame for the stall image and ID
        title_frame = ctk.CTkFrame(info_window, fg_color="#E5ECFA", corner_radius=10)
        title_frame.pack(pady=(10, 0), padx=20, fill="x")
        # Create a frame for the stall image and ID
        image_frame = ctk.CTkFrame(info_window, fg_color="white", corner_radius=10)
        image_frame.pack(pady=10, padx=20, fill="x")

        # Stall ID label (above the image)
        stall_id_label = ctk.CTkLabel(
            title_frame, text=f"Stall ID: {stall_id}",
            font=("Arial", 22, "bold"), text_color="black", fg_color="#E5ECFA", pady=20
        )
        stall_id_label.pack()

        # Display the stall image
        if stall_image_path:
            img = Image.open(stall_image_path)
            img = img.resize((300, 300), Image.Resampling.LANCZOS)  # Resize the image
            photo = ImageTk.PhotoImage(img)
            image_label = Label(image_frame, image=photo, bg="white")
            image_label.image = photo  # Keep a reference to avoid garbage collection
            image_label.pack(pady=5)

        # Create a frame for the stall details
        stall_info_frame = ctk.CTkFrame(info_window, fg_color="white", corner_radius=10)
        stall_info_frame.pack(pady=10, padx=20, fill="both", expand=True)
        details_frame = ctk.CTkFrame(stall_info_frame, fg_color="white", corner_radius=10)
        details_frame.pack(anchor='center')

        # Stall Size
        size_label = ctk.CTkLabel(
            details_frame, text=f"Size: {size}",
            fg_color="white", font=("Arial", 14, 'bold'), text_color="black"
        )
        size_label.pack(anchor="w", pady=5, padx=10)

        # Location
        location_label = ctk.CTkLabel(
            details_frame, text=f"Location: {location}",
            fg_color="white", font=("Arial", 14, 'bold'), text_color="black"
        )
        location_label.pack(anchor="w", pady=5, padx=10)

        # Latitude and Longitude
        latitude_label = ctk.CTkLabel(
            details_frame, text=f"Latitude: {latitude}",
            fg_color="white", font=("Arial", 14, 'bold'), text_color="black"
        )
        latitude_label.pack(anchor="w", pady=5, padx=10)

        longitude_label = ctk.CTkLabel(
            details_frame, text=f"Longitude: {longitude}",
            fg_color="white", font=("Arial", 14, 'bold'), text_color="black"
        )
        longitude_label.pack(anchor="w", pady=5, padx=10)

        # Rent Price
        rent_price_label = ctk.CTkLabel(
            details_frame, text=f"Rent Price: RM{rent_price}",
            fg_color="white", font=("Arial", 14, 'bold'), text_color="black"
        )
        rent_price_label.pack(anchor="w", pady=5, padx=10)
    else:
        messagebox.showerror("Error", "No information found for this stall.")

    # Close button at the bottom
    close_button = ctk.CTkButton(info_window, text="Close", command=info_window.destroy, fg_color="#F47070",
                                 text_color="white")
    close_button.bind("<Enter>", lambda e: close_button.configure(fg_color="#FF7575"))
    close_button.bind("<Leave>", lambda e: close_button.configure(fg_color="#F47070"))
    close_button.pack(pady=10)


def edit_stall(stall):
    global image_label  # Declare the variable as global to avoid it being garbage collected

    # Clear the content frame
    for widget in content_frame.winfo_children():
        widget.destroy()

    full_frame = Frame(content_frame, bg="#D3CAFF", padx=20, pady=10, bd=2, relief='groove')
    full_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Fields for editing stall details
    edit_frame = ctk.CTkFrame(full_frame, fg_color="#F0ECFF")
    edit_frame.pack(side="top", anchor="center", expand=True, padx=10, pady=10)

    # Title Label
    title_label = ctk.CTkLabel(edit_frame, text="Edit Stall Information", font=("Bauhaus 93", 22), fg_color="#F0ECFF")
    title_label.grid(row=0, column=0, columnspan=3, pady=5)

    # Unpack stall data into meaningful variable names
    stall_id, location, size, rent_price_per_month, latitude, longitude, stall_image = stall

    # Stall Location
    ctk.CTkLabel(edit_frame, text="Location", font=('times new roman', 12), fg_color="#F0ECFF").grid(row=1, column=0,
                                                                                                     padx=10, pady=10,
                                                                                                     sticky="e")
    location_entry = ctk.CTkEntry(edit_frame, font=('times new roman', 12))
    location_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
    location_entry.insert(0, location)

    # Stall Size
    ctk.CTkLabel(edit_frame, text="Size", font=('times new roman', 12), fg_color="#F0ECFF").grid(row=2, column=0,
                                                                                                 padx=10, pady=10,
                                                                                                 sticky="e")
    size_entry = ctk.CTkEntry(edit_frame, font=('times new roman', 12))
    size_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")
    size_entry.insert(0, size)

    # Rent Price
    ctk.CTkLabel(edit_frame, text="Rent Price per Month", font=('times new roman', 12), fg_color="#F0ECFF").grid(row=3,
                                                                                                                 column=0,
                                                                                                                 padx=10,
                                                                                                                 pady=10,
                                                                                                                 sticky="e")
    rent_price_per_month_entry = ctk.CTkEntry(edit_frame, font=('times new roman', 12))
    rent_price_per_month_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")
    rent_price_per_month_entry.insert(0, rent_price_per_month)

    # Latitude and Longitude
    ctk.CTkLabel(edit_frame, text="Latitude", font=('times new roman', 12), fg_color="#F0ECFF").grid(row=4, column=0,
                                                                                                     padx=10, pady=10,
                                                                                                     sticky="e")
    latitude_entry = ctk.CTkEntry(edit_frame, font=('times new roman', 12))
    latitude_entry.grid(row=4, column=1, padx=10, pady=10, sticky="w")
    latitude_entry.insert(0, latitude)

    ctk.CTkLabel(edit_frame, text="Longitude", font=('times new roman', 12), fg_color="#F0ECFF").grid(row=5, column=0,
                                                                                                      padx=10, pady=10,
                                                                                                      sticky="e")
    longitude_entry = ctk.CTkEntry(edit_frame, font=('times new roman', 12))
    longitude_entry.grid(row=5, column=1, padx=10, pady=10, sticky="w")
    longitude_entry.insert(0, longitude)

    # Image Path and Select Button
    ctk.CTkLabel(edit_frame, text="Stall Image", font=('times new roman', 12), fg_color="#F0ECFF").grid(row=6, column=0,
                                                                                                        padx=10,
                                                                                                        pady=10,
                                                                                                        sticky="e")
    entry_image_path = ctk.CTkEntry(edit_frame, font=('times new roman', 12))
    entry_image_path.grid(row=6, column=1, padx=10, pady=10, sticky="w")
    entry_image_path.insert(0, stall_image)

    # Image Label for display
    image_label = Label(edit_frame, bg="#F0ECFF")
    image_label.grid(row=0, column=2, rowspan=8, padx=10)

    # Function to load and display the image
    def load_image(image_path):
        if os.path.exists(image_path):
            # Load image using Pillow
            image = Image.open(image_path)
            image = image.resize((250, 250), Image.Resampling.LANCZOS)  # Resize to fit the display
            photo = ImageTk.PhotoImage(image)

            # Update image label
            image_label.config(image=photo)
            image_label.image = photo  # Keep a reference to avoid garbage collection
        else:
            image_label.config(text="No image found", fg="red")

    # Load image when the form is loaded
    load_image(stall_image)

    # Buttons (Select Image, Select Lat/Long, Clear Fields)
    buttons_frame = ctk.CTkFrame(edit_frame, fg_color="#F0ECFF")
    buttons_frame.grid(row=7, column=0, columnspan=3, pady=10)

    ctk.CTkButton(buttons_frame, text="Select Image", command=lambda: select_image(entry_image_path, image_label),
                  font=("Arial", 16, "bold"),
                  fg_color="#C2AEF7", hover_color="#C8B3FF", text_color="white").pack(side='left', padx=10)

    ctk.CTkButton(buttons_frame, text="Select Lat/Long",
                  command=lambda: open_map_window(latitude_entry, longitude_entry), font=("Arial", 16, "bold"),
                  fg_color="#6DA397", hover_color="#83C4B6", text_color="white").pack(side='left', padx=10)

    def update_stall():
        new_location = location_entry.get()
        new_size = size_entry.get()
        new_rent_price_per_month = rent_price_per_month_entry.get()
        new_latitude = latitude_entry.get()
        new_longitude = longitude_entry.get()
        new_image_path = entry_image_path.get()

        try:
            # Update the stall information in the database (including image path and coordinates)
            stall = Stall(conn, cursor)
            stall.update_stall(stall_id, new_location, new_size, new_rent_price_per_month, new_latitude, new_longitude, new_image_path)

            load_image(new_image_path)  # Reload the updated image
            stalls_admin()  # Go back to stall list
        except Exception as e:
            messagebox.showerror("Error", f"Error updating stall: {str(e)}")

    ctk.CTkButton(edit_frame, text="Update Stall", command=update_stall, font=("Arial", 16, "bold"),
                  fg_color="#A0E388", hover_color="#A9F090", text_color="white").grid(row=8, column=0, columnspan=3,
                                                                                      pady=10)

    # Back button
    ctk.CTkButton(edit_frame, text="Back to Stalls", command=stalls_admin, font=("Arial", 16, "bold"),
                  fg_color="#F5D27E", hover_color="#FFDA83", text_color="white").grid(row=9, column=0, columnspan=3,
                                                                                      pady=5)

    # Clear button functionality
    def clear_fields():
        location_entry.delete(0, END)
        size_entry.delete(0, END)
        rent_price_per_month_entry.delete(0, END)
        latitude_entry.delete(0, END)
        longitude_entry.delete(0, END)
        entry_image_path.delete(0, END)
        image_label.config(image='', text="No image selected", fg="red")

    ctk.CTkButton(buttons_frame, text="Clear Fields", command=clear_fields, font=("Arial", 16, "bold"),
                  fg_color="#EB7F7F", hover_color="#FF8A8A", text_color="white").pack(side='left', padx=10)


def add_stall():
    # Clear the content frame
    for widget in content_frame.winfo_children():
        widget.destroy()

    full_frame = Frame(content_frame, bg="#D3CAFF", padx=20, pady=10, bd=2, relief='groove')
    full_frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Frame for fields
    add_frame = ctk.CTkFrame(full_frame, fg_color="#FFFFFF", corner_radius=10)
    add_frame.pack(side="top", anchor="center", expand=True, padx=10, pady=5)

    # Title Label
    title_label = ctk.CTkLabel(add_frame, text="Add New Stall", font=("Bauhaus 93", 22))
    title_label.grid(row=0, column=0, columnspan=5, pady=15)

    # Stall Location
    location_entry = ctk.CTkEntry(add_frame, placeholder_text="Enter stall location", width=200)
    location_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
    location_label = ctk.CTkLabel(add_frame, text="Location", font=("Arial", 12))
    location_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

    # Stall Size
    size_entry = ctk.CTkEntry(add_frame, placeholder_text="Enter stall size", width=200)
    size_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")
    size_label = ctk.CTkLabel(add_frame, text="Size", font=("Arial", 12))
    size_label.grid(row=2, column=0, padx=10, pady=10, sticky="e")

    # Rent Price
    rent_price_per_month_entry = ctk.CTkEntry(add_frame, placeholder_text="Enter rent price per month", width=200)
    rent_price_per_month_entry.grid(row=3, column=1, padx=10, pady=10, sticky="w")
    rent_price_label = ctk.CTkLabel(add_frame, text="Rent Price per Month", font=("Arial", 12))
    rent_price_label.grid(row=3, column=0, padx=10, pady=10, sticky="e")

    # Latitude
    latitude_entry = ctk.CTkEntry(add_frame, placeholder_text="Enter latitude", width=200)
    latitude_entry.grid(row=4, column=1, padx=10, pady=10, sticky="w")
    latitude_label = ctk.CTkLabel(add_frame, text="Latitude", font=("Arial", 12))
    latitude_label.grid(row=4, column=0, padx=10, pady=10, sticky="e")

    # Longitude
    longitude_entry = ctk.CTkEntry(add_frame, placeholder_text="Enter longitude", width=200)
    longitude_entry.grid(row=5, column=1, padx=10, pady=10, sticky="w")
    longitude_label = ctk.CTkLabel(add_frame, text="Longitude", font=("Arial", 12))
    longitude_label.grid(row=5, column=0, padx=10, pady=10, sticky="e")

    # Stall Image
    entry_image_path = ctk.CTkEntry(add_frame, placeholder_text="Enter image path", width=200)
    entry_image_path.grid(row=6, column=1, padx=10, pady=10, sticky="w")
    stall_image_label = ctk.CTkLabel(add_frame, text="Stall Image", font=("Arial", 12))
    stall_image_label.grid(row=6, column=0, padx=10, pady=10, sticky="e")

    # Image label display
    image_label = Label(add_frame, text="", bg="#FFFFFF")
    image_label.grid(row=0, column=2, rowspan=8, padx=10)

    def insert_stall():
        # Get values from entries
        location = location_entry.get().strip()
        size = size_entry.get().strip()
        rent_price_per_month = rent_price_per_month_entry.get().strip()
        latitude = latitude_entry.get().strip()
        longitude = longitude_entry.get().strip()
        image_path = entry_image_path.get().strip()

        # Check if any of the entries still contain placeholder values or are empty
        if (location == "" or location == location_entry.cget("placeholder_text") or
                size == "" or size == size_entry.cget("placeholder_text") or
                rent_price_per_month == "" or rent_price_per_month == rent_price_per_month_entry.cget(
                    "placeholder_text") or
                latitude == "" or latitude == latitude_entry.cget("placeholder_text") or
                longitude == "" or longitude == longitude_entry.cget("placeholder_text") or
                image_path == "" or image_path == entry_image_path.cget("placeholder_text")):
            messagebox.showerror("Error", "Please fill out all fields with valid information.")
            return  # Exit the function if placeholders are found

        try:
            # Retrieve admin_id based on logged-in username
            username = logged_in_user['username']
            cursor.execute("SELECT admin_id FROM admin WHERE username = ?", (username,))
            result = cursor.fetchone()

            if result:
                admin_id = result[0]

                # Insert the new stall with admin_id into the database
                stall = Stall(conn, cursor)
                stall.add_stall(location, size, rent_price_per_month, latitude, longitude, image_path, admin_id)

                # Clear all fields after successful insertion
                location_entry.delete(0, 'end')
                size_entry.delete(0, 'end')
                rent_price_per_month_entry.delete(0, 'end')
                latitude_entry.delete(0, 'end')
                longitude_entry.delete(0, 'end')
                entry_image_path.delete(0, 'end')
                image_label.configure(text="")

                # Call the stalls function to display the stall list
                stalls_admin()
            else:
                messagebox.showerror("Error", "Admin not found.")

        except Exception as e:
            messagebox.showerror("Error", f"Error adding stall: {str(e)}")

    # Buttons Frame
    buttons_frame = ctk.CTkFrame(add_frame, fg_color="#FFFFFF")
    buttons_frame.grid(row=7, column=0, columnspan=3, pady=10)

    # Select Image Button
    select_image_btn = ctk.CTkButton(buttons_frame, text="Select Image",
                                     command=lambda: select_image(entry_image_path, image_label), fg_color='#C2AEF7',
                                     text_color='white', font=('Arial', 16, 'bold'))
    select_image_btn.bind("<Enter>", lambda e: select_image_btn.configure(fg_color="#C8B3FF"))
    select_image_btn.bind("<Leave>", lambda e: select_image_btn.configure(fg_color="#C2AEF7"))
    select_image_btn.pack(side='left', padx=10)

    # Select Latitude/Longitude Button
    select_lat_btn = ctk.CTkButton(buttons_frame, text="Select Lat/Long",
                                   command=lambda: open_map_window(latitude_entry, longitude_entry), fg_color='#6DA397',
                                   text_color='white', font=('Arial', 16, 'bold'))
    select_lat_btn.bind("<Enter>", lambda e: select_lat_btn.configure(fg_color="#83C4B6"))
    select_lat_btn.bind("<Leave>", lambda e: select_lat_btn.configure(fg_color="#6DA397"))
    select_lat_btn.pack(side='left', padx=10)

    # Clear Fields Button
    clear_btn = ctk.CTkButton(buttons_frame, text="Clear Fields",
                              command=lambda: [location_entry.delete(0, 'end'), size_entry.delete(0, 'end'),
                                               rent_price_per_month_entry.delete(0, 'end'),
                                               latitude_entry.delete(0, 'end'),
                                               longitude_entry.delete(0, 'end'), entry_image_path.delete(0, 'end'),
                                               image_label.configure(text="")], fg_color='#EB7F7F', text_color='white',
                              font=('Arial', 16, 'bold'))
    clear_btn.bind("<Enter>", lambda e: clear_btn.configure(fg_color="#FF8A8A"))
    clear_btn.bind("<Leave>", lambda e: clear_btn.configure(fg_color="#EB7F7F"))
    clear_btn.pack(side='left', padx=10)

    # Add Stall Button
    add_stall_btn = ctk.CTkButton(add_frame, text="Add Stall", command=insert_stall, fg_color='#A0E388',
                                  text_color='white', font=('Arial', 16, 'bold'))
    add_stall_btn.bind("<Enter>", lambda e: add_stall_btn.configure(fg_color="#A9F090"))
    add_stall_btn.bind("<Leave>", lambda e: add_stall_btn.configure(fg_color="#A0E388"))
    add_stall_btn.grid(row=8, column=0, columnspan=3, pady=10)

    # Back to Stalls Button
    back_btn = ctk.CTkButton(add_frame, text="Back to Stalls", command=lambda: stalls_admin(), fg_color='#F5D27E',
                             text_color='white', font=('Arial', 16, 'bold'))
    back_btn.bind("<Enter>", lambda e: back_btn.configure(fg_color="#FFDA83"))
    back_btn.bind("<Leave>", lambda e: back_btn.configure(fg_color="#F5D27E"))
    back_btn.grid(row=9, columnspan=5, pady=5)


def open_map_window(latitude_entry, longitude_entry):
    # Create a new window for the map
    map_window = Toplevel()
    map_window.title("Map")

    # Set up the map view
    map_widget = TkinterMapView(map_window, width=600, height=400, corner_radius=0)
    map_widget.pack(fill="both", expand=True)

    # Set initial position to Penang, Malaysia and zoom level
    map_widget.set_position(5.4164, 100.3327)  # Penang, Malaysia
    map_widget.set_zoom(10)  # Set initial zoom level

    # Store the current marker
    marker = None
    selected_latitude = None
    selected_longitude = None

    # Function to place a marker when the user clicks on the map
    def on_map_click(lat, lon):
        nonlocal marker, selected_latitude, selected_longitude

        # Remove the previous marker if any
        if marker:
            marker.delete()

        # Set the marker at the clicked position
        marker = map_widget.set_marker(lat, lon, text=f"Lat: {lat}, Lon: {lon}")

        # Store the selected latitude and longitude
        selected_latitude = lat
        selected_longitude = lon

        # Update the coordinates display (non-clickable)
        info_label.config(text=f"{lat:.6f}, {lon:.6f}")

    # Add a right-click menu option to select the location and place a marker
    def handle_right_click(lat, lon):
        on_map_click(lat, lon)

    # Right-click event listener to get coordinates
    map_widget.add_right_click_menu_command(
        label="Select this location",
        command=lambda coords: handle_right_click(*coords),
        pass_coords=True  # Ensure the coordinates are passed to the command
    )

    # Label to show the coordinates (non-clickable)
    info_label = Label(map_window, text="Right-click to select a location")
    info_label.pack(pady=5)

    # Button to paste the coordinates into the entries
    paste_button = Button(map_window, text="Paste Coordinates",
                          command=lambda: paste_coordinates(latitude_entry, longitude_entry), bg='#93AEFF')
    paste_button.pack(pady=5)

    def paste_coordinates(latitude_entry, longitude_entry):
        if selected_latitude is not None and selected_longitude is not None:
            latitude_entry.delete(0, 'end')  # Clear the entry first
            longitude_entry.delete(0, 'end')
            latitude_entry.insert(0, str(selected_latitude))  # Insert selected latitude
            longitude_entry.insert(0, str(selected_longitude))  # Insert selected longitude
            map_window.destroy()  # Close the map window after pasting

    # Button to close the window
    close_button = Button(map_window, text="Close", command=map_window.destroy, bg='#99F0FF')
    close_button.pack(pady=10)


def select_image(entry_image_path, image_label):
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")])
    if file_path:
        entry_image_path.delete(0, END)
        entry_image_path.insert(0, file_path)

        try:
            image = Image.open(file_path)
            width, height = image.size

            # Crop the image to a square
            if width > height:
                left = (width - height) / 2
                top = 0
                right = (width + height) / 2
                bottom = height
            else:
                left = 0
                top = (height - width) / 2
                right = width
                bottom = (height + width) / 2

            image = image.crop((left, top, right, bottom)).resize((250, 250), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            image_label.config(image=photo)
            image_label.image = photo
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")


# Live location
@app.route('/')
def index():
    # Serve the homepage with the map
    return render_template('live_location.html')  # This will serve the map

def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371  # Radius of Earth in kilometers
    return c * r * 1000  # Return distance in meters

@app.route('/update_location', methods=['POST'])
def update_location():
    data = request.json
    latitude = data['latitude']
    longitude = data['longitude']
    scan_status = data.get('scan_status', 'recognized')
    username = logged_in_user.get('username')

    if not username:
        return jsonify({"error": "No username found"}), 400

    conn = sqlite3.connect('stall_rental_system.db')
    cursor = conn.cursor()

    try:
        # Get tenant ID
        cursor.execute("SELECT tenant_id FROM tenant WHERE username = ?", (username,))
        tenant_info = cursor.fetchone()

        if not tenant_info:
            return jsonify({"error": "Tenant not found"}), 404

        tenant_id = tenant_info[0]

        # Get stall information
        cursor.execute("""
            SELECT s.stall_id, s.latitude, s.longitude 
            FROM rental r 
            JOIN stall s ON r.stall_id = s.stall_id 
            WHERE r.tenant_id = ? 
        """, (tenant_id,))
        stall_info = cursor.fetchone()

        if not stall_info:
            return jsonify({"error": "Stall not found for tenant"}), 404

        stall_id, stall_latitude, stall_longitude = stall_info
        distance = haversine(latitude, longitude, stall_latitude, stall_longitude)
        threshold_distance = 100  # meters
        attendance_status = "Correct Location" if distance <= threshold_distance else "Wrong Location"
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Check for existing record TODAY using DATE function
        cursor.execute("""
            SELECT attendance_records_id, attendance_count 
            FROM attendance_records 
            WHERE tenant_id = ? 
            AND stall_id = ? 
            AND DATE(attendance_time) = DATE(?)
        """, (tenant_id, stall_id, current_time))

        existing_record = cursor.fetchone()

        if existing_record:
            # Update existing record
            attendance_records_id, current_count = existing_record
            new_count = current_count + 1

            cursor.execute("""
                UPDATE attendance_records 
                SET latitude = ?,
                    longitude = ?,
                    attendance_time = ?,
                    attendance_status = ?,
                    attendance_count = ?,
                    scan_status = ?
                WHERE attendance_records_id = ?
            """, (latitude, longitude, current_time, attendance_status,
                  new_count, scan_status, attendance_records_id))

            message = "Attendance updated."
        else:
            # Check total attendance count for today
            cursor.execute("""
                SELECT COUNT(*) 
                FROM attendance_records 
                WHERE tenant_id = ? 
                AND DATE(attendance_time) = DATE(?)
            """, (tenant_id, current_time))

            attendance_count = cursor.fetchone()[0]

            if attendance_count < 3:
                # Insert new record
                cursor.execute("""
                    INSERT INTO attendance_records (
                        tenant_id, stall_id, latitude, longitude,
                        attendance_time, attendance_status, attendance_count, scan_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (tenant_id, stall_id, latitude, longitude, current_time,
                      attendance_status, attendance_count + 1, scan_status))

                message = "Attendance recorded."
            else:
                return jsonify({"error": "Maximum attendance limit reached for today."}), 403

        conn.commit()

        # Show appropriate messagebox based on attendance status and scan status
        if attendance_status == "Correct Location" and scan_status == "recognized":
            messagebox.showinfo("Success",
                                f"{message} Received location: {latitude}, {longitude} for tenant ID: {tenant_id}.")
        elif scan_status == "unrecognized":
            messagebox.showwarning("Warning", "Face scan does not match the logged-in tenant.")

        elif attendance_status == "Wrong Location":
            messagebox.showwarning("Warning",
                                   f"Location is too far from the stall location. Distance: {distance:.2f} meters. - {message}")

        return jsonify({
            "status": message,
            "attendance_status": attendance_status,
            "scan_status": scan_status
        }), 200

    except Exception as e:
        print(f"Error in update_location: {str(e)}")
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()

def connect_db():
    # Database connection function
    return sqlite3.connect('stall_rental_system.db')

@app.route('/get_tenant_stalls', methods=['GET'])
def get_tenant_stalls():
    # Endpoint to get tenant stalls
    conn = connect_db()
    cursor = conn.cursor()

    # Query to fetch tenants with their rented stalls
    query = """
    SELECT 
        t.username, 
        ar.latitude AS tenant_latitude, 
        ar.longitude AS tenant_longitude, 
        s.stall_id, 
        s.latitude AS stall_latitude, 
        s.longitude AS stall_longitude 
    FROM tenant t
    JOIN attendance_records ar ON t.tenant_id = ar.tenant_id
    JOIN rental r ON t.tenant_id = r.tenant_id
    JOIN stall s ON r.stall_id = s.stall_id
    """

    cursor.execute(query)
    result = cursor.fetchall()

    # Prepare the response
    tenant_stalls = [
        {
            "username": row[0],
            "tenant_latitude": row[1],
            "tenant_longitude": row[2],
            "stall_id": row[3],
            "stall_latitude": row[4],
            "stall_longitude": row[5]
        }
        for row in result
    ]

    conn.close()
    return jsonify(tenant_stalls)

@app.route('/get_stall_location', methods=['GET'])
def get_stall_location():
    # Get the username of the logged-in user
    username = logged_in_user.get('username')  # Assuming logged_in_user is a global variable

    if not username:
        return jsonify({"error": "No username found"}), 400

    # Connect to the database and get the tenant_id based on the username
    conn = sqlite3.connect('stall_rental_system.db')
    cursor = conn.cursor()

    cursor.execute("SELECT tenant_id FROM tenant WHERE username = ?", (username,))
    tenant_info = cursor.fetchone()

    if tenant_info:
        tenant_id = tenant_info[0]

        # Get the stall associated with the tenant
        cursor.execute("SELECT stall_id FROM rental WHERE tenant_id = ?", (tenant_id,))
        stall_info = cursor.fetchone()

        if stall_info:
            stall_id = stall_info[0]

            # Get the stall's location (latitude and longitude)
            cursor.execute("SELECT latitude, longitude FROM stall WHERE stall_id = ?", (stall_id,))
            stall_location = cursor.fetchone()

            if stall_location:
                latitude, longitude = stall_location
                return jsonify({"latitude": latitude, "longitude": longitude}), 200
            else:
                return jsonify({"error": "Stall location not found"}), 404
        else:
            return jsonify({"error": "No active rental found for tenant."}), 404
    else:
        return jsonify({"error": "Tenant not found"}), 404

    conn.close()

def open_browser():
    # Function to open the browser
    webbrowser.open_new('http://127.0.0.1:5000')

def start_flask(scan_status="recognized"):
    threading.Thread(target=lambda: app.run(debug=True, use_reloader=False)).start()
    webbrowser.open_new(f'http://127.0.0.1:5000/?status={scan_status}')


# Tenant
def tenant_dashboard():
    def add_rounded_corners(image, radius):
        # Create a mask for rounded corners
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)

        # Draw a rounded rectangle
        draw.rounded_rectangle([0, 0, image.size[0], image.size[1]], radius=radius, fill=255)

        # Apply the mask to the image to make the corners rounded
        rounded_image = ImageOps.fit(image, image.size)
        rounded_image.putalpha(mask)

        return rounded_image

    attendance_button = None

    def stall():
        global attendance_button, stall_frame,details_frame  # Declare attendance_button as global to modify its state in take_attendance
        username = logged_in_user.get('username')
        if username is None:
            print("No username found in logged_in_user.")
            return

        # Connect to your database
        conn = sqlite3.connect('stall_rental_system.db')
        cursor = conn.cursor()

        # Clear previous content
        for widget in content_frame.winfo_children():
            widget.destroy()

        # Create a frame for stall details and center it
        stall_frame = Frame(content_frame, bg="#C7D3FF", padx=20, pady=10, bd=2, relief='groove')
        stall_frame.pack(fill='both', expand=True)

        # Retrieve tenant ID based on username for attendance check
        cursor.execute("SELECT tenant_id FROM tenant WHERE username = ?", (username,))
        tenant_id = cursor.fetchone()[0]

        # Get the current date
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        # Fetch attendance_count and latest attendance status for the current date
        cursor.execute(""" 
            SELECT attendance_count, MAX(attendance_status), MAX(scan_status)
            FROM attendance_records 
            WHERE tenant_id = ? AND DATE(attendance_time) = ? 
        """, (tenant_id, current_date))
        attendance_count, last_status, scan_status = cursor.fetchone()

        # Check if attendance_count is None, initialize to 0 if necessary
        attendance_count = attendance_count if attendance_count is not None else 0

        # Disable the attendance button if limit reached or correct location with recognized scan status
        attendance_taken = attendance_count >= 3 or (last_status == "Correct Location" and scan_status == "recognized")

        # Retrieve rental information for the tenant
        cursor.execute(""" 
            SELECT stall.stall_image, stall.stall_id, stall.location, stall.size, 
                   stall.rent_price_per_month, rental.start_date, rental.end_date
            FROM rental
            JOIN stall ON rental.stall_id = stall.stall_id
            WHERE rental.tenant_id = ?
        """, (tenant_id,))
        rental_info = cursor.fetchone()

        current_date = datetime.date.today()
        if rental_info:
            stall_image_path, stall_id, location, size, rent_price_per_month, start_date, end_date = rental_info

            if end_date and datetime.datetime.strptime(end_date, '%Y-%m-%d').date() < current_date:
                prompt_renewal(stall_id, stall_image_path, location, end_date, tenant_id)
                return

            # Display the stall image
            image = Image.open(stall_image_path)
            image = image.resize((500, 500), Image.Resampling.LANCZOS)
            rounded_image = add_rounded_corners(image, radius=30)
            image_tk = ImageTk.PhotoImage(rounded_image)

            center_frame = ctk.CTkFrame(stall_frame, fg_color="#C7D3FF")
            center_frame.pack(fill='both', expand=True, padx=10, pady=10)

            image_frame = ctk.CTkFrame(center_frame, fg_color="#CFCFCF", border_color="#A8A8A8", border_width=2)
            image_frame.pack(side='left', padx=10, pady=10, fill='both', expand=True)

            image_label = Label(image_frame, image=image_tk, bg="#CFCFCF")
            image_label.image = image_tk
            image_label.pack(pady=10, padx=10,expand=True)

            details_frame = ctk.CTkFrame(center_frame, fg_color="#CFCFCF", border_color="#A8A8A8", border_width=2)
            details_frame.pack(side='right', padx=10, pady=10, fill='both', expand=True)

            # Display stall details
            info_frame = ctk.CTkFrame(details_frame, fg_color="#DEDEDE", border_color="#A8A8A8", border_width=2)
            info_frame.pack(pady=10, anchor='center',expand=True)

            details = [
                ("Stall ID:", stall_id, "image\\apply_stall.png"),
                ("Location:", location, "image\\location.png"),
                ("Size:", size, "image\\size.png"),
                ("Rent Price per Month:", f"RM{rent_price_per_month:.2f}", "image\\price.png"),
                ("Rental Period:", f"{start_date} to {end_date if end_date else 'Ongoing'}", "image\\attendance.png")
            ]

            for label_text, value, icon_path in details:
                row_frame = ctk.CTkFrame(info_frame, fg_color="#CFCFCF")
                row_frame.pack(pady=10, padx=10, anchor='center')

                icon_image = Image.open(icon_path)
                icon_image = icon_image.resize((20, 20), Image.Resampling.LANCZOS)
                icon_tk = ImageTk.PhotoImage(icon_image)

                icon_label = Label(row_frame, image=icon_tk, bg="#CFCFCF")
                icon_label.image = icon_tk
                icon_label.pack(side='left', padx=5)

                Label(row_frame, text=label_text, font=('Arial', 12, 'bold'), bg="#CFCFCF", fg="blue").pack(
                    side='left', padx=5)
                Label(row_frame, text=value, font=('Arial', 12, 'bold'), bg="#CFCFCF", fg="black").pack(
                    side='left', padx=5)

            # Create the attendance button
            attendance_button = ctk.CTkButton(details_frame, text="Take Attendance", command=take_attendance,
                                              font=("Arial", 20, "bold"), fg_color='#00527B', hover_color="#007AB8",
                                              text_color='white', corner_radius=50,
                                              state='disabled' if attendance_taken else 'normal')
            attendance_button.pack(pady=10)

            def ToggleToAttendanceHistory(event=None):
                if stall_frame is not None:
                    stall_frame.destroy()
                view_attendance_history()

            # Button to view attendance history
            attendance_history_button = Label(
                details_frame, text="View Attendance History", bg="#CFCFCF", fg="darkblue", font=("Arial", 10)
            )
            attendance_history_button.bind('<Enter>', lambda event: attendance_history_button.config(
                font=('arial', 10, 'underline')))
            attendance_history_button.bind('<Leave>',
                                           lambda event: attendance_history_button.config(font=('arial', 10)))
            attendance_history_button.bind('<Button-1>', ToggleToAttendanceHistory)
            attendance_history_button.pack(pady=10)

            # Display a message if attendance limit reached or already recorded
            if attendance_taken:
                message = "Attendance limit reached for today." if attendance_count >= 3 else "Attendance already recorded as Correct Location with recognized scan."
                message_label = Label(details_frame, text=message, font=('Arial', 12, 'italic'), bg="#CFCFCF", fg="red")
                message_label.pack(pady=5)

                def twinkle_message():
                    current_color = message_label.cget("fg")
                    next_color = "#C7D3FF" if current_color == "red" else "red"
                    message_label.config(fg=next_color)
                    message_label.after(500, twinkle_message)

                twinkle_message()

        else:
            # No rental information available
            twinkle_label = Label(stall_frame, text="No stall rented currently.", font=('Arial', 18, 'italic'),
                                  bg="#C7D3FF", fg="#FF0000")
            twinkle_label.pack(pady=20)

            def twinkle():
                current_color = twinkle_label.cget("fg")
                next_color = "#CFCFCF" if current_color == "#FF0000" else "#FF0000"
                twinkle_label.config(fg=next_color)
                stall_frame.after(500, twinkle)

            twinkle()

        conn.close()

    def prompt_renewal(stall_id, stall_image_path, location, expired_date, tenant_id):
        # Clear previous frame content
        for widget in stall_frame.winfo_children():
            widget.destroy()

        renew_contract_frame = Frame(stall_frame, bg="#C7D3FF", padx=20, pady=10, bd=2, relief='groove')
        renew_contract_frame.pack(side='top', pady=10)

        # Display a renewal prompt message
        Label(renew_contract_frame, text="Your rental has expired. Would you like to renew?",
              font=('Arial', 14, 'bold'),
              bg="#C7D3FF", fg="red").pack(side='top', pady=10)

        def delete_rental():
            conn = sqlite3.connect("stall_rental_system.db")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rental WHERE tenant_id = ? AND stall_id = ?", (tenant_id, stall_id))
            conn.commit()
            conn.close()

        def on_yes():
            # Delete the expired rental record
            delete_rental()
            # Display the renewal form
            display_renewal_form()

        def on_no():
            # Delete the expired rental record and return to the main screen
            delete_rental()
            messagebox.showinfo("Cancellation", "Your stall rental has been canceled.")
            stall()

        button_frame = Frame(renew_contract_frame, bg="#C7D3FF", padx=20, pady=10)
        button_frame.pack(side='bottom', pady=10)

        # Yes button
        yes_button = ctk.CTkButton(button_frame, text="Yes", command=on_yes, fg_color="#46B85D", hover_color="#52D96E",
                                   text_color="white")
        yes_button.pack(side="left", padx=10, pady=10)

        # No button
        no_button = ctk.CTkButton(button_frame, text="No", command=on_no, fg_color="#D95252", hover_color="#F25C5C",
                                  text_color="white")
        no_button.pack(side="right", padx=10, pady=10)

        def display_renewal_form():
            conn = sqlite3.connect("stall_rental_system.db")
            cursor = conn.cursor()

            cursor.execute("SELECT fullname, ic FROM tenant WHERE username = ?", (logged_in_user['username'],))
            tenant_info = cursor.fetchone()
            conn.close()

            if tenant_info:
                fullname, tenant_ic = tenant_info
            else:
                fullname, tenant_ic = "Unknown", "Unknown"

            # Clear existing widgets for the renewal form
            for widget in stall_frame.winfo_children():
                widget.destroy()

            # Display stall image
            image = Image.open(stall_image_path)
            image = image.resize((300, 250), Image.Resampling.LANCZOS)
            image_tk = ImageTk.PhotoImage(image)
            image_label = Label(stall_frame, image=image_tk, bg="#C7D3FF")
            image_label.image = image_tk
            image_label.pack(pady=10)

            #center
            center_frame = Frame(stall_frame, bg="#C7D3FF")
            center_frame.pack(anchor="center", pady=5)

            # Display tenant details for renewal
            tenant_name_frame = Frame(center_frame, bg="#C7D3FF")
            tenant_name_frame.pack(anchor="w", pady=5)
            Label(tenant_name_frame, text="Tenant Name:", font=('Arial', 12, 'bold'), bg="#C7D3FF", fg="#3B5998").pack(
                side="left")
            Label(tenant_name_frame, text=fullname, font=('Arial', 12), bg="#C7D3FF", fg="#1C1C1C").pack(side="left")

            ic_frame = Frame(center_frame, bg="#C7D3FF")
            ic_frame.pack(anchor="w", pady=5)
            Label(ic_frame, text="IC:", font=('Arial', 12, 'bold'), bg="#C7D3FF", fg="#3B5998").pack(side="left")
            Label(ic_frame, text=tenant_ic, font=('Arial', 12), bg="#C7D3FF", fg="#1C1C1C").pack(side="left")

            # Display stall details for renewal
            stall_id_frame = Frame(center_frame, bg="#C7D3FF")
            stall_id_frame.pack(anchor="w", pady=5)
            Label(stall_id_frame, text="Stall ID:", font=('Arial', 12, 'bold'), bg="#C7D3FF", fg="#3B5998").pack(
                side="left")
            Label(stall_id_frame, text=stall_id, font=('Arial', 12), bg="#C7D3FF", fg="#1C1C1C").pack(side="left")

            location_frame = Frame(center_frame, bg="#C7D3FF")
            location_frame.pack(anchor="w", pady=5)
            Label(location_frame, text="Location:", font=('Arial', 12, 'bold'), bg="#C7D3FF", fg="#3B5998").pack(
                side="left")
            Label(location_frame, text=location, font=('Arial', 12), bg="#C7D3FF", fg="#1C1C1C").pack(side="left")

            start_date_frame = Frame(center_frame, bg="#C7D3FF")
            start_date_frame.pack(anchor="w", pady=5)
            Label(start_date_frame, text="Start Date:", font=('Arial', 12, 'bold'), bg="#C7D3FF", fg="#3B5998").pack(
                side="left")
            Label(start_date_frame, text=expired_date, font=('Arial', 12), bg="#C7D3FF", fg="#1C1C1C").pack(side="left")

            # Renewal duration selection with dropdown (1-12 months)
            ctk.CTkLabel(stall_frame, text="Select Renewal Duration (months):", fg_color="#C7D3FF").pack(pady=5)
            duration_combobox = ctk.CTkComboBox(stall_frame, values=[str(i) for i in range(1, 13)], state="readonly")
            duration_combobox.pack(pady=5)
            duration_combobox.set("1")  # Set default value to 1 month

            def submit_renewal():
                try:
                    duration = int(duration_combobox.get())

                    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    conn = sqlite3.connect("stall_rental_system.db")
                    cursor = conn.cursor()

                    cursor.execute(
                        "INSERT INTO applications (tenant_id, stall_id, reason, start_date, duration, status, application_date) VALUES (?, ?, 'renew contract', ?, ?, 'pending',?)",
                        (tenant_id, stall_id, expired_date, duration, current_time)
                    )
                    conn.commit()
                    conn.close()

                    messagebox.showinfo("Success", "Renewal application submitted!")
                    stall()  # Return to main stall function
                except ValueError:
                    messagebox.showerror("Error", "Invalid duration entered!")

            ctk.CTkButton(stall_frame, text="Submit Renewal", command=submit_renewal, fg_color="#00527B", text_color="white",hover_color="#0077B3").pack(pady=10)

    def view_attendance_history():
        # Clear previous content from content_frame
        for widget in content_frame.winfo_children():
            widget.destroy()  # Clear the content frame before displaying the calendar and map

        # Create a new frame for attendance history
        attendance_frame = Frame(content_frame, bg="#D3CAFF", bd=2, padx=20, pady=10, relief='groove')
        attendance_frame.pack(fill="both", expand=True)

        Label(attendance_frame, text="Attendance History", bg="#D3CAFF", font=("Bauhaus 93", 18)).pack(pady=(5, 0))
        # Label for date selection
        Label(attendance_frame, text="Select Date:", bg="#D3CAFF").pack(pady=(10, 0))

        # Calendar for selecting date with DD-MM-YYYY format, default to today's date
        today = datetime.datetime.now()
        date_entry = DateEntry(attendance_frame, date_pattern="dd-MM-yyyy", year=today.year, month=today.month,
                               day=today.day)
        date_entry.pack(pady=(0, 10))

        # Confirm button to fetch and display attendance
        confirm_button = ctk.CTkButton(attendance_frame, text="Confirm",
                                       command=lambda: display_attendance_map(date_entry.get_date(), attendance_frame),
                                       fg_color="#00699E", hover_color="#0085C7")
        confirm_button.pack(pady=10)

    def display_attendance_map(selected_date, attendance_frame):
        # Clear previous content from attendance_frame (if you want to reset only the map)
        for widget in attendance_frame.winfo_children():
            if isinstance(widget, Frame) and widget.winfo_name() == "map_frame":
                widget.destroy()  # Clear the existing map frame if it exists

        # Create a new frame for the map display
        map_frame = Frame(attendance_frame, bg="#D3CAFF", padx=20, relief='groove', name="map_frame")
        map_frame.pack(fill="both", expand=True, padx=10)

        # Initialize the map widget
        map_widget = TkinterMapView(map_frame, width=600, height=300, corner_radius=0)
        map_widget.pack(fill="both", expand=True)

        # Retrieve tenant ID and rental information
        username = logged_in_user.get('username')
        cursor.execute("SELECT tenant_id, fullname FROM tenant WHERE username = ?", (username,))
        tenant_data = cursor.fetchone()
        tenant_id, fullname = tenant_data[0], tenant_data[1]

        # Initialize default values for attendance status and colors
        status_text = "No Attendance"
        attendance_color = "gray"
        tenant_lat, tenant_lon = None, None  # Default location

        # Retrieve tenant's location, attendance status, and scan status on the selected date from attendance records
        cursor.execute(""" 
            SELECT latitude, longitude, attendance_status, scan_status FROM attendance_records 
            WHERE tenant_id = ? AND DATE(attendance_time) = ? 
        """, (tenant_id, selected_date))
        attendance_data = cursor.fetchone()

        # Retrieve stall location
        cursor.execute("""
            SELECT stall.latitude, stall.longitude
            FROM rental
            JOIN stall ON rental.stall_id = stall.stall_id
            WHERE rental.tenant_id = ?
        """, (tenant_id,))
        stall_location = cursor.fetchone()

        # Set map initial view based on a central location (Penang, Malaysia)
        map_widget.set_position(5.4164, 100.3327)
        map_widget.set_zoom(10)

        # Determine marker color based on attendance status and scan status if attendance data exists
        if attendance_data:
            tenant_lat, tenant_lon, attendance_status, scan_status = attendance_data

            if scan_status == "unrecognized":
                status_text = "Unrecognized Face"
                attendance_color = "#C4B800"
                tenant_marker_color = "#C4B800"  # Set marker color for unrecognized face
            else:
                status_text = "Correct Location" if attendance_status == "Correct Location" else "Wrong Location"
                attendance_color = "green" if attendance_status == "Correct Location" else "red"
                tenant_marker_color = "green" if attendance_status == "Correct Location" else "red"

        # Add tenant location marker if coordinates are available
        if tenant_lat is not None and tenant_lon is not None:
            map_widget.set_marker(tenant_lat, tenant_lon, text="Tenant's Location",
                                  marker_color_circle=tenant_marker_color,
                                  marker_color_outside=tenant_marker_color)

        # Add stall location marker if it exists
        if stall_location:
            stall_lat, stall_lon = stall_location
            map_widget.set_marker(stall_lat, stall_lon, text="Stall Location",
                                  marker_color_circle="blue", marker_color_outside="blue")

        # Close map button and status labels
        bottom_frame = ctk.CTkFrame(map_frame)
        bottom_frame.pack(pady=10, fill='x')

        close_map_button = ctk.CTkButton(bottom_frame, text="Close Map", command=stall, fg_color="red",
                                         hover_color="#F25C5C",
                                         text_color="white")
        close_map_button.pack(side='left', padx=10, pady=5)

        # Attendance status label
        attendance_status_text = f"You {'got' if attendance_data else 'did not'} take attendance on {selected_date.strftime('%d-%m-%Y')}."
        attendance_status_label = Label(bottom_frame, text=attendance_status_text, bg="#D3CAFF")
        attendance_status_label.pack(side='left', padx=10)

        # Tenant full name and attendance status
        attendance_info_label = Label(bottom_frame, text=f"{fullname}: {status_text}", bg="#D3CAFF",
                                      fg=attendance_color)
        attendance_info_label.pack(side='left', padx=10)

        # Status labels (optional)
        status_labels = {
            'Wrong Location': ('Wrong Location', 'red'),
            'Correct Location': ('Correct Location', 'green'),
            'Unrecognized Face': ('Unrecognized Face', '#C4B800'),
            'Stall Location': ('Stall Location', 'blue')
        }

        status_frame = Frame(bottom_frame, bg="#D3CAFF")
        status_frame.pack(side='right', fill="x")

        for status, (text, color) in status_labels.items():
            status_label = Label(status_frame, text=text, bg=color, fg="white", padx=10, pady=5)
            status_label.pack(side="right", padx=5)

    def take_attendance():
        global attendance_button

        if 'username' not in logged_in_user or not logged_in_user['username']:
            messagebox.showerror("Error", "No tenant is currently logged in.")
            return

        logged_in_username = logged_in_user['username']

        conn = sqlite3.connect('stall_rental_system.db')
        cursor = conn.cursor()

        cursor.execute("SELECT tenant_id FROM tenant WHERE username = ?", (logged_in_username,))
        tenant_id = cursor.fetchone()[0]

        # Get the current date for attendance check
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        # Check today's attendance count, last attendance status, and scan status
        cursor.execute("""
                    SELECT attendance_count, MAX(attendance_status), MAX(scan_status)
                    FROM attendance_records
                    WHERE tenant_id = ? AND DATE(attendance_time) = ?
                """, (tenant_id, current_date))
        attendance_data = cursor.fetchone()

        attendance_count = attendance_data[0] if attendance_data[0] is not None else 0
        last_status = attendance_data[1]
        last_scan_status = attendance_data[2]

        # Check if attendance should be blocked based on attendance count, status, and scan status
        attendance_taken = attendance_count >= 3 or (
                    last_status == "Correct Location" and last_scan_status == "recognized")

        def twinkle_message():
            current_color = message_label.cget("fg")
            next_color = "#CFCFCF" if current_color == "red" else "red"
            message_label.config(fg=next_color)
            message_label.after(500, twinkle_message)

        if attendance_taken:
            message = "Attendance limit reached for today." if attendance_count >= 3 else "Attendance already recorded as Correct Location."
            message_label = Label(details_frame, text=message, font=('Arial', 12, 'italic'), bg="#CFCFCF", fg="red")
            message_label.pack(pady=5)
            messagebox.showinfo(
                "Attendance Status",
                message
            )
            attendance_button.configure(state='disabled')
            twinkle_message()  # Start twinkling
            conn.close()
            return

        # Continue with face recognition and location check as needed
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                messagebox.showerror("Error", "Could not open webcam.")
                return

            messagebox.showinfo("Info", "Please press 's' to capture your face.")

            while True:
                ret, frame = cap.read()
                if not ret:
                    messagebox.showerror("Error", "Failed to capture face image.")
                    break

                cv2.imshow("Webcam", frame)
                if cv2.waitKey(1) & 0xFF == ord('s'):
                    break

            cap.release()
            cv2.destroyAllWindows()

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(frame_rgb)
            if not face_locations:
                messagebox.showerror("Error", "No face detected. Please try again.")
                return

            face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)
            if not face_encodings:
                messagebox.showerror("Error", "Failed to encode face. Please try again.")
                return

            captured_encoding = face_encodings[0]
            recognized_username = verify_face_embedding(captured_encoding)

            if recognized_username and recognized_username == logged_in_username:
                messagebox.showinfo("Success", f"Face recognized. Welcome, {recognized_username}!")
                start_flask()

                # Re-check attendance limit and update label if necessary
                if attendance_taken:
                    attendance_button.configure(state='disabled')
                    twinkle_message()
            else:
                messagebox.showerror("Error", "Face not recognized. Map will display with a yellow marker.")
                start_flask("unrecognized")

                # Re-check attendance limit and update label if necessary
                if attendance_taken:
                    attendance_button.configure(state='disabled')
                    twinkle_message()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during face recognition: {e}")
            print(f"Error details: {e}")

        conn.close()

    def apply_stall():
        # Clear existing widgets
        for widget in content_frame.winfo_children():
            widget.destroy()

        apply_stall_frame = Frame(content_frame, bg="#C7D3FF", padx=20, pady=10, bd=2, relief='groove')
        apply_stall_frame.pack(fill='both', expand=True)

        # Create a label for the frame
        Label(apply_stall_frame, text="Available Stalls", font=('Bauhaus 93', 18, 'bold'), bg="#C7D3FF").pack(pady=10)

        # Search stalls by ID
        def search_stalls():
            search_term = search_entry.get()
            if search_term.isdigit():
                cursor.execute(
                    "SELECT stall_id, stall_image, rent_price_per_month, size FROM stall WHERE stall_id = ? AND stall_id NOT IN (SELECT stall_id FROM rental)",
                    (search_term,)
                )
                search_results = cursor.fetchall()
                display_stalls(search_results)
            else:
                display_stalls(stalls)

        # Search field and button
        search_frame = ctk.CTkFrame(apply_stall_frame)
        search_frame.pack(pady=10)

        search_entry = ctk.CTkEntry(search_frame, width=200, placeholder_text="Enter Stall ID")
        search_entry.pack(side='left', padx=10)

        search_button = ctk.CTkButton(search_frame, text="Search", command=search_stalls, fg_color="#00699E",
                                      hover_color="#0085C7")
        search_button.pack(side='left')

        # Function to toggle filter frame visibility
        def toggle_filter_frame():
            if filter_frame.winfo_ismapped():
                filter_frame.pack_forget()  # Hide the filter frame if it's currently shown
            else:
                filter_frame.pack(side='top', pady=10)  # Show the filter frame below the search frame

        filter_icon = ctk.CTkImage(Image.open("image\\filter.png"), size=(20, 20))
        location_icon = ctk.CTkImage(Image.open("image\\location.png"), size=(20, 20))
        # Add the Filter button
        filter_button = ctk.CTkButton(search_frame, image=filter_icon, text="", command=toggle_filter_frame, width=10,
                                      fg_color="#8288FF", hover_color="#9BA5FF")
        filter_button.pack(side='left', padx=10)

        # Filter frame that will appear below the search frame when the filter button is clicked
        filter_frame = ctk.CTkFrame(apply_stall_frame)
        filter_frame.pack_forget()  # Initially hide the filter frame

        # Create filter widgets in the filter frame
        min_price_label = ctk.CTkLabel(filter_frame, text="Min Price (RM):")
        min_price_label.pack(side='left', padx=10)

        min_price_entry = ctk.CTkEntry(filter_frame, width=100)
        min_price_entry.pack(side='left', padx=10)

        max_price_label = ctk.CTkLabel(filter_frame, text="Max Price (RM):")
        max_price_label.pack(side='left', padx=10)

        max_price_entry = ctk.CTkEntry(filter_frame, width=100)
        max_price_entry.pack(side='left', padx=10)

        # Filter stalls by price
        def filter_stalls():
            min_price = min_price_entry.get()
            max_price = max_price_entry.get()

            query = """
                SELECT stall_id, stall_image, rent_price_per_month, size 
                FROM stall 
                WHERE stall_id NOT IN (SELECT stall_id FROM rental)
                AND stall_id NOT IN (SELECT stall_id FROM applications WHERE status = 'pending')
            """
            params = []

            # Apply price filters if provided
            if min_price.isdigit():
                query += " AND rent_price_per_month >= ?"
                params.append(min_price)
            if max_price.isdigit():
                query += " AND rent_price_per_month <= ?"
                params.append(max_price)

            cursor.execute(query, params)
            filtered_stalls = cursor.fetchall()
            display_stalls(filtered_stalls)

        # Add "Apply Filter" button to the filter frame
        apply_filter_button = ctk.CTkButton(filter_frame, text="Apply Filter", command=filter_stalls,
                                            fg_color="#00699E", hover_color="#0085C7")
        apply_filter_button.pack(side='left', padx=10)

        def fetch_stalls():
            conn = sqlite3.connect("stall_rental_system.db")
            cursor = conn.cursor()

            # Query to get stall statuses based on the rental and applications tables
            cursor.execute("""
                SELECT s.stall_id, s.latitude, s.longitude, 
                       CASE 
                           -- Stall is occupied (exists in the rental table)
                           WHEN r.rental_id IS NOT NULL THEN 'occupied' 
                           -- Stall has a pending application
                           WHEN a.application_id IS NOT NULL AND a.status = 'pending' THEN 'pending' 
                           -- Stall is neither rented nor has a pending application
                           ELSE 'available' 
                       END AS status
                FROM stall s
                -- Left join with rental to check if the stall is rented
                LEFT JOIN rental r ON s.stall_id = r.stall_id
                -- Left join with applications to check if the stall has a pending application
                LEFT JOIN applications a ON s.stall_id = a.stall_id AND a.status = 'pending'
            """)

            # Fetch all results
            stalls = cursor.fetchall()
            conn.close()
            return stalls

        def open_map_view():
            for widget in content_frame.winfo_children():
                widget.destroy()  # Clear the content frame before displaying the map

            map_frame = Frame(content_frame, bg="#D3CAFF", padx=20, pady=10, bd=2, relief='groove')
            map_frame.pack(fill="both", expand=True)

            map_widget = TkinterMapView(map_frame, width=600, height=400, corner_radius=0)
            map_widget.pack(fill="both", expand=True)

            # Set initial position and zoom for the map (Penang, Malaysia)
            map_widget.set_position(5.4164, 100.3327)
            map_widget.set_zoom(10)

            # Fetch stalls and add markers based on their status
            stalls = fetch_stalls()

            for stall_id, lat, lon, status in stalls:
                if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                    print(f"Skipping invalid coordinates for Stall ID: {stall_id} (Lat: {lat}, Lon: {lon})")
                    continue

                marker_text = f"Stall ID: {stall_id}"

                if status == 'occupied':
                    marker_color = "red"
                elif status == 'pending':
                    marker_color = "#C4B800"
                else:
                    marker_color = "green"

                map_widget.set_marker(lat, lon, text=marker_text, marker_color_circle=marker_color,
                                      marker_color_outside=marker_color)

            bottom_frame = ctk.CTkFrame(map_frame)
            bottom_frame.pack(pady=10, fill='x')

            # Status display labels
            status_frame = Frame(bottom_frame)
            status_frame.pack(anchor='e', pady=5, padx=(30, 10))

            status_labels = {
                'occupied': ('Occupied', 'red'),
                'pending': ('Pending', '#C4B800'),
                'available': ('Available', 'green')
            }

            for status, (text, color) in status_labels.items():
                status_label = Label(status_frame, text=text, bg=color, fg="white", padx=10, pady=5)
                status_label.pack(side="right", padx=5)

            # Close button
            close_map_button = ctk.CTkButton(bottom_frame, text="Close Map", command=apply_stall, fg_color="red",
                                             text_color="white", hover_color="#ED6E6E")
            close_map_button.pack(anchor='center', pady=5, padx=10)

        # Add the Map button
        map_button = ctk.CTkButton(search_frame, image=location_icon, text="", command=open_map_view, width=10,
                                   fg_color="#A3B3DE", hover_color="#B4C5F5")  # Adjust the command if needed
        map_button.pack(side='right', padx=10)  # Add some padding between buttons

        # Create a frame to hold the canvas and scrollbar
        container_frame = Frame(apply_stall_frame)
        container_frame.pack(fill='both', expand=True)

        canvas = Canvas(container_frame)
        canvas.pack(side='left', fill='both', expand=True)

        scrollbar = Scrollbar(container_frame, orient='vertical', command=canvas.yview)
        scrollbar.pack(side='right', fill='y')

        canvas.configure(yscrollcommand=scrollbar.set)

        stalls_frame = ctk.CTkFrame(canvas)
        canvas_window = canvas.create_window((0, 0), window=stalls_frame, anchor='nw')

        stalls_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind('<Configure>', lambda event: canvas.itemconfig(canvas_window, width=event.width))

        # Fetch and display available stalls
        def display_stalls(stalls):
            # Clear previous stall display
            for widget in stalls_frame.winfo_children():
                widget.destroy()

            if not stalls:
                ctk.CTkLabel(stalls_frame, text="No stall found with the given ID", font=ctk.CTkFont(size=12)).pack(
                    pady=10)
                return

            for stall in stalls:
                stall_id, stall_image, rent_price, size = stall

                stall_frame = ctk.CTkFrame(stalls_frame, corner_radius=10)
                stall_frame.pack(side='top', fill='x', padx=10, pady=10)

                def add_rounded_corners(image, radius):
                    mask = Image.new('L', image.size, 0)
                    draw = ImageDraw.Draw(mask)
                    draw.rounded_rectangle([0, 0, image.size[0], image.size[1]], radius=radius, fill=255)
                    rounded_image = ImageOps.fit(image, image.size)
                    rounded_image.putalpha(mask)
                    return rounded_image

                # Process the image
                image = Image.open(stall_image)
                image = image.resize((200, 200), Image.Resampling.LANCZOS)
                rounded_image = add_rounded_corners(image, radius=30)
                stall_photo = ctk.CTkImage(light_image=rounded_image, dark_image=rounded_image, size=(200, 200))

                # Display the stall image
                stall_image_label = ctk.CTkLabel(stall_frame, image=stall_photo, text="")
                stall_image_label.image = stall_photo  # Prevent garbage collection
                stall_image_label.pack(side='left', pady=10, padx=10)

                # Details frame
                details_frame = ctk.CTkFrame(stall_frame, fg_color="transparent")
                details_frame.pack(side='left', padx=10)

                # Icons for each detail
                icons = {
                    "stall_id": "image\\apply_stall.png",  # Path to your icon images
                    "price": "image\\price.png",
                    "size": "image\\size.png"
                }

                # Helper to add detail with icon
                def add_detail_with_icon(frame, icon_path, label_text, value_text, label_color, value_color):
                    detail_frame = ctk.CTkFrame(frame, fg_color="transparent")
                    detail_frame.pack(anchor='w', fill='x')

                    icon_image = Image.open(icon_path).resize((20, 20), Image.Resampling.LANCZOS)
                    icon_photo = ctk.CTkImage(light_image=icon_image, dark_image=icon_image, size=(20, 20))

                    icon_label = ctk.CTkLabel(detail_frame, image=icon_photo, text="")
                    icon_label.image = icon_photo  # Prevent garbage collection
                    icon_label.pack(side='left', padx=5)

                    text_label = ctk.CTkLabel(detail_frame, text=label_text, font=('arial',12,'bold'),
                                              text_color=label_color)
                    text_label.pack(side='left', padx=5)

                    value_label = ctk.CTkLabel(detail_frame, text=value_text, font=('arial',12,'bold'),
                                               text_color=value_color)
                    value_label.pack(side='left')

                # Add details with icons and colors
                add_detail_with_icon(details_frame, icons["stall_id"], "Stall ID:", stall_id, "#16417C", "#2D86FF")
                add_detail_with_icon(details_frame, icons["price"], "Price:", f"RM{rent_price:.2f}/month", "#16417C",
                                     "#2D86FF")
                add_detail_with_icon(details_frame, icons["size"], "Size:", size, "#16417C", "#2D86FF")

                # Function to display more stall information #add stall map
                def show_stall_info(stall_id):
                    # Fetch specific stall information from the database
                    cursor.execute(
                        "SELECT stall_id, stall_image, location, size, rent_price_per_month, latitude, longitude FROM stall WHERE stall_id = ?",
                        (stall_id,))
                    stall_info = cursor.fetchone()

                    if stall_info:
                        # Unpack the stall information into meaningful variable names
                        stall_id, stall_image, location, size, rent_price, latitude, longitude = stall_info

                        # Create a new window for stall info using customtkinter
                        stall_info_window = Toplevel()  # Create a new customtkinter window
                        stall_info_window.title(f"Stall Information - ID: {stall_id}")
                        stall_info_window.geometry("1920x1080+0+0")
                        stall_info_window.state("zoomed")
                        stall_info_window.configure(bg="#F1F3FA")

                        # Add a header
                        header_frame = ctk.CTkFrame(stall_info_window, fg_color="#4267B2", corner_radius=10)
                        header_frame.pack(fill='x', padx=20, pady=(20, 10))
                        header_label = ctk.CTkLabel(header_frame, text=f"Stall ID: {stall_id}",
                                                    font=ctk.CTkFont(size=20, weight="bold"), text_color="white")
                        header_label.pack(pady=10)

                        # Create a frame to hold both the stall image and the map
                        content_frame = ctk.CTkFrame(stall_info_window, fg_color="white", corner_radius=10)
                        content_frame.pack(pady=10, padx=20, fill="both", expand=True)

                        # Create a sub-frame to hold the image and map closer together
                        sub_content_frame = ctk.CTkFrame(content_frame, fg_color="white", corner_radius=10)
                        sub_content_frame.pack(anchor="center")

                        # Stall image frame
                        image_frame = ctk.CTkFrame(sub_content_frame, fg_color="white", corner_radius=10)
                        image_frame.pack(side='left', padx=10, pady=10)  # Adjust padding for closeness

                        # Load and resize the stall image
                        image = Image.open(stall_image)  # Use the unpacked variable for the stall image
                        image = image.resize((300, 300), Image.Resampling.LANCZOS)

                        # Add rounded corners to the image
                        rounded_image = add_rounded_corners(image, radius=30)  # Adjust the radius for desired curvature

                        # Convert to CTkImage
                        stall_photo = ctk.CTkImage(light_image=rounded_image, dark_image=rounded_image, size=(300, 300))

                        # Display the rounded image
                        image_label = ctk.CTkLabel(image_frame, image=stall_photo, text="")
                        image_label.image = stall_photo  # Keep a reference to avoid garbage collection
                        image_label.pack(pady=15)

                        # Create a frame for the map next to the image
                        map_frame = ctk.CTkFrame(sub_content_frame, fg_color="white", corner_radius=10)
                        map_frame.pack(side='left', padx=10, pady=10)  # Adjust padding for closeness

                        # Initialize Mapbox map widget
                        map_widget = TkinterMapView(map_frame, width=400, height=300, corner_radius=0)
                        map_widget.pack(fill="both", expand=True)

                        # Set the position of the map based on the latitude and longitude of the stall
                        map_widget.set_position(latitude, longitude)
                        map_widget.set_zoom(15)  # Adjust zoom level as necessary

                        # Add a marker for the specific stall
                        marker_text = f"Stall ID: {stall_id}"
                        map_widget.set_marker(latitude, longitude, text=marker_text, marker_color_circle="blue",
                                              marker_color_outside="blue")

                        # Stall information labels with improved layout and padding
                        # Load icons for labels (you need to have these icons in the project directory)
                        location_icon = ctk.CTkImage(
                            Image.open("image\\location.png").resize((30, 30), Image.Resampling.LANCZOS))
                        size_icon = ctk.CTkImage(
                            Image.open("image\\size.png").resize((30, 30), Image.Resampling.LANCZOS))
                        rent_icon = ctk.CTkImage(
                            Image.open("image\\price.png").resize((30, 30), Image.Resampling.LANCZOS))
                        latitude_icon = ctk.CTkImage(
                            Image.open("image\\latitude.png").resize((30, 30), Image.Resampling.LANCZOS))
                        longitude_icon = ctk.CTkImage(
                            Image.open("image\\longitude.png").resize((30, 30), Image.Resampling.LANCZOS))

                        # Stall information frame
                        stall_info_frame = ctk.CTkFrame(stall_info_window, fg_color="white", corner_radius=10)
                        stall_info_frame.pack(pady=10, padx=20, fill="both", expand=True)
                        info_frame = ctk.CTkFrame(stall_info_frame, fg_color="white", corner_radius=10)
                        info_frame.pack(anchor="center")

                        # Helper function to create a row with an icon and text in the same column
                        def create_info_row(icon, text, value, row):
                            label = ctk.CTkLabel(
                                info_frame,
                                image=icon,
                                text=f" {text}: {value}",
                                font=ctk.CTkFont(size=18),
                                compound="left",  # Display icon to the left of the text
                                anchor="w"
                            )
                            label.grid(row=row, column=0, sticky='w', padx=10, pady=5)

                        # Display stall information with icons
                        create_info_row(location_icon, "Location", location, 0)
                        create_info_row(size_icon, "Size", size, 1)
                        create_info_row(rent_icon, "Rent Price", f"RM{rent_price:.2f}/month", 2)
                        create_info_row(latitude_icon, "Latitude", latitude, 3)
                        create_info_row(longitude_icon, "Longitude", longitude, 4)

                        # Add a "Close" button to close the window
                        button_frame = ctk.CTkFrame(stall_info_window, fg_color="transparent")
                        button_frame.pack(pady=20, padx=20, fill="x", anchor="center")  # Centered button frame

                        close_button = ctk.CTkButton(button_frame, text="Close", font=('times new roman', 22, 'bold'),
                                                     corner_radius=10, command=stall_info_window.destroy,
                                                     fg_color="#00699E", hover_color="#0085C7")
                        close_button.pack(pady=10)

                # Add the Apply button
                apply_button = ctk.CTkButton(stall_frame, text="Apply", command=lambda id=stall_id: apply_for_stall(id),
                                             fg_color="#8288FF", hover_color="#9BA5FF")
                apply_button.pack(side='right', padx=10)

                # Add the Stall Information button
                info_button = ctk.CTkButton(stall_frame, text="Stall Info",
                                            command=lambda id=stall_id: show_stall_info(id), fg_color="#00699E",
                                            hover_color="#0085C7")
                info_button.pack(side='right', padx=10)

        # Fetch available stalls from the database
        cursor.execute(
            "SELECT stall_id, stall_image, rent_price_per_month, size FROM stall "
            "WHERE stall_id NOT IN (SELECT stall_id FROM rental) "
            "AND stall_id NOT IN (SELECT stall_id FROM applications WHERE status = 'pending')"
        )
        stalls = cursor.fetchall()

        # Display all stalls initially
        display_stalls(stalls)

    def apply_for_stall(stall_id):

        # Check if the logged-in tenant already has an active rental
        cursor.execute(
            "SELECT stall_id FROM rental WHERE tenant_id = (SELECT tenant_id FROM tenant WHERE username = ?)",
            (logged_in_user['username'],)
        )
        existing_rental = cursor.fetchone()

        if existing_rental:
            messagebox.showerror("Stall Application", "You already have a rented stall.")
            return

        # Check if the logged-in tenant already has a pending application
        cursor.execute(
            "SELECT stall_id FROM applications WHERE tenant_id = (SELECT tenant_id FROM tenant WHERE username = ?) AND status = 'pending'",
            (logged_in_user['username'],)
        )
        pending_application = cursor.fetchone()

        if pending_application:
            messagebox.showerror("Stall Application", "You already have a pending application for another stall.")
            return

        MenuFrame.destroy()

        # Retrieve the stall image path from the database based on the stall_id
        cursor.execute("SELECT stall_image FROM stall WHERE stall_id = ?", (stall_id,))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", "No stall found with the given Stall ID.")
            return

        stall_image_path = result[0]  # Assuming the first column is the image path

        # Fetch tenant's full name and IC
        cursor.execute("SELECT fullname, ic FROM tenant WHERE username = ?", (logged_in_user['username'],))
        tenant_info = cursor.fetchone()

        if tenant_info:
            tenant_fullname, tenant_ic = tenant_info
        else:
            messagebox.showerror("Error", "Unable to retrieve tenant information.")
            return

        # Show form for the tenant to fill out
        application_window = Toplevel()  # Create a new window for the application form
        application_window.title(f"Stall Application - Stall ID: {stall_id}")
        application_window.geometry("1920x1080+0+0")
        application_window.state("zoomed")
        application_window.configure(bg="#F2F2F2")  # Light gray background

        # Frame for Stall ID
        stall_id_frame = ctk.CTkFrame(application_window, corner_radius=10,
                                      fg_color="#007ACC")  # Blue frame for Stall ID
        stall_id_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(stall_id_frame, text=f"Stall ID: {stall_id}", font=("Arial", 24, 'bold'), text_color='white').pack(
            pady=10)

        # Frame for Stall Image
        stall_image_frame = ctk.CTkFrame(application_window, corner_radius=10,
                                         fg_color="white")  # Light salmon frame for Image
        stall_image_frame.pack(pady=10, padx=10, fill="x")

        # Load and display the stall image below Stall ID
        try:
            image = Image.open(stall_image_path)
            resized_image = image.resize((300, 200), Image.Resampling.LANCZOS)  # Resize image to fit the window

            # Create a mask for the rounded corners
            mask = Image.new('L', resized_image.size, 0)
            draw = ImageDraw.Draw(mask)
            draw.rounded_rectangle((0, 0, resized_image.size[0], resized_image.size[1]),
                                   radius=30, fill=255)  # Adjust radius for corner roundness

            # Apply the mask to the image
            rounded_image = Image.new('RGBA', resized_image.size)
            rounded_image.paste(resized_image, (0, 0), mask)

            # Create a PhotoImage object to display in CTk
            stall_image = ImageTk.PhotoImage(rounded_image)
            image_label = Label(stall_image_frame, image=stall_image, bg="white")  # Show image
            image_label.image = stall_image  # Keep a reference to avoid garbage collection
            image_label.pack(pady=10)
        except Exception as e:
            messagebox.showerror("Image Error", f"Could not load image: {e}")

        # Frame for Application Form
        info_frame = ctk.CTkFrame(application_window, corner_radius=10,
                                  fg_color="white")  # Light green frame for Form
        info_frame.pack(pady=10, padx=10, fill="both", expand=True)

        application_form_frame = ctk.CTkFrame(info_frame, corner_radius=10,
                                              fg_color="white")  # Light green frame for Form
        application_form_frame.pack(anchor='center')

        ctk.CTkLabel(application_form_frame, text=f"Tenant:", font=("Arial", 16, 'bold'),
                     text_color='#333').grid(row=0, column=0, sticky='e', padx=(10, 5), pady=(10, 0))

        ctk.CTkLabel(application_form_frame, text=f"{tenant_fullname}",
                     font=("Arial", 16, 'bold'),
                     text_color='#333').grid(row=0, column=1, sticky='w', padx=(10, 5), pady=(10, 0))

        ctk.CTkLabel(application_form_frame, text=f"IC:  {tenant_ic}",
                     font=("Arial", 16, 'bold'),
                     text_color='#333').grid(row=0, column=2, sticky='w', pady=(10, 0))

        # Start date selection
        ctk.CTkLabel(application_form_frame, text="Start Date:", font=("Arial", 16, 'bold'), text_color='#333').grid(
            row=1, column=0, sticky='e', padx=(10, 5), pady=10)
        start_date_entry = DateEntry(application_form_frame, width=12, background='darkblue',
                                     foreground='white', borderwidth=2, date_pattern='y-mm-dd',
                                     mindate=datetime.datetime.today())  # Start date defaults to today
        start_date_entry.grid(row=1, column=1, sticky='w', pady=10, padx=(5, 10))

        # Duration dropdown (1 to 12 months)
        ctk.CTkLabel(application_form_frame, text="Duration (Months):", font=("Arial", 16, 'bold'),
                     text_color='#333').grid(row=2, column=0, sticky='e', padx=(10, 5), pady=10)
        duration_options = [str(i) for i in range(1, 13)]  # 1 to 12 months
        duration_menu = ctk.CTkOptionMenu(application_form_frame, values=duration_options)
        duration_menu.grid(row=2, column=1, sticky='w', pady=10, padx=(5, 10))

        # Reason for application with customtkinter's CTkTextbox
        ctk.CTkLabel(application_form_frame, text="Reason for Application:", font=("Arial", 16, 'bold'),
                     text_color='#333').grid(row=3, column=0, sticky='ne', padx=(10, 5), pady=10)
        reason_text = ctk.CTkTextbox(application_form_frame, height=100, width=500, fg_color='#C0C0C0',
                                     text_color='black', font=("Arial", 14))
        reason_text.grid(row=3, column=1, columnspan=2, pady=10, padx=(5, 10))

        # Agreement checkbox and label
        agree_var = BooleanVar()
        agree_checkbox = ctk.CTkCheckBox(application_form_frame, text="I agree to the terms and conditions",
                                         variable=agree_var)
        agree_checkbox.grid(row=4, column=1, pady=10)

        # Agreement label to open the agreement window
        agreement_label = ctk.CTkLabel(application_form_frame, text="Read the agreement",
                                       font=("Arial", 12, "underline"), text_color="#007ACC", cursor="hand2")
        agreement_label.grid(row=4, column=2, pady=10, sticky='w')
        agreement_label.bind("<Button-1>", lambda e: show_agreement())  # Bind click event to show agreement

        # Agreement label to open the agreement window
        def show_agreement():
            agreement_window = Toplevel(application_window)
            agreement_window.title("Agreement")
            agreement_window.geometry("1920x1080+0+0")
            agreement_window.state("zoomed")
            agreement_window.configure(bg="#F2F2F2")

            title_frame = ctk.CTkFrame(agreement_window, corner_radius=10,
                                       fg_color="#007ACC")  # Blue frame for Stall ID
            title_frame.pack(pady=10, padx=10, fill="x")

            ctk.CTkLabel(title_frame, text=f"Terms and Conditions:", font=("Arial", 22, 'bold'),
                         text_color='white').pack(pady=10)

            agreement_text = """
            1. You agree to follow all rules and regulations set forth by the governing authority.
            2. The stall should be used for its intended purpose only, as specified in the rental contract.
            3. The rental period is fixed, and any extension must be requested at least 30 days in advance.
            4. The tenant is responsible for any damages caused to the stall and surrounding property.
            5. Violation of any terms may result in the immediate termination of the rental agreement and forfeiture of the security deposit.
            6. The tenant must maintain the stall in a clean and orderly condition, complying with all health and safety standards.
            7. All sales or services conducted in the stall must adhere to legal standards, including obtaining any necessary permits or licenses.
            8. Any modifications or alterations to the stall must be approved in writing by the governing authority.
            9. The tenant agrees not to sublet or transfer stall ownership rights to any other party without prior approval.
            10. The governing authority reserves the right to inspect the stall at any time to ensure compliance with these terms.
            11. In the event of a natural disaster or other unforeseen circumstances, the governing authority may terminate the rental agreement without liability for compensation.
            12. Payment of rent must be made on or before the due date specified in the contract. Late payments may incur penalties or late fees.
            13. The tenant is expected to cooperate with neighboring stall operators to maintain a harmonious environment.
            14. Any advertising or signage must be approved by the governing authority and should not obstruct the view or operation of other stalls.
            15. The tenant must attend any meetings or training sessions as required by the governing authority to ensure compliance and safety standards.
            16. The tenant is required to take attendance daily using the authorized system, which includes providing a live location and face scan for verification purposes.
            17. If the tenant's attendance shows an incorrect location or an incorrect face scan is detected, the governing authority reserves the right to send an auditor to verify the tenant's
                presence and compliance at the stall.
            """

            label = ctk.CTkLabel(agreement_window, text=agreement_text, height=300, width=500, fg_color='#C0C0C0',
                                 text_color='black', font=("Arial", 18), anchor="nw", justify="left", corner_radius=10)
            label.pack(pady=10, padx=10, expand=True, fill='both')

            # Close button
            close_button = ctk.CTkButton(agreement_window, text="Close", command=agreement_window.destroy,
                                         fg_color='#FF4D4D', hover_color='#CC0000', text_color='white',
                                         font=("Arial", 14))
            close_button.pack(pady=10)

        # Submit button for the application
        def submit_application():
            if not agree_var.get():
                messagebox.showerror("Stall Application",
                                     "You must agree to the terms and conditions to submit the application.")
                return

            start_date = start_date_entry.get()
            duration = duration_menu.get()
            reason = reason_text.get("1.0", "end").strip()  # Get all text from the Text widget

            if not reason or not duration:
                messagebox.showerror("Stall Application", "Please fill out all fields correctly.")
                return

            # Get the current date and time
            application_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Insert application into the applications table
            applications = Applications(conn, cursor)
            applications.insert_application(logged_in_user, stall_id, reason, duration, start_date, application_date)

            # Fetch tenant email
            cursor.execute("SELECT tenant_id, fullname, email_address FROM tenant WHERE username = ?",
                           (logged_in_user['username'],))
            tenant_data = cursor.fetchone()

            if tenant_data:
                tenant_id, tenant_fullname, tenant_email = tenant_data  # Extract the email from the fetched row

                # Prepare tenant email body
                tenant_subject = f"New Stall Application for Stall ID {stall_id}"
                tenant_body = f"Dear {tenant_fullname},\n\nYour application for Stall ID: {stall_id} has been successfully submitted.\n\nApplication Details:\n- Start Date: {start_date}\n- Duration: {duration} months\n- Reason: {reason} \n\nWe will notify you once your application is reviewed.\n\n\nBest regards,\nGovernment Stall Rental System"
                send_email_notification(tenant_email, tenant_subject, tenant_body)

                tenant_notification_message = f"Dear Tenant,\n\nYour application for Stall ID {stall_id} has been submitted successfully.\nDetails:\n- Start Date: {start_date}\n- Duration: {duration} months\n- Reason: {reason}\n\n\nBest regards,\nGovernment Stall Rental System"
                insert_notification("tenant", tenant_id, tenant_notification_message)

                # Send email notification to the admin
                admin_email = 'projectall2.2024@gmail.com'  # Replace with the actual admin email
                admin_subject = f"New Stall Application for Stall ID {stall_id}"
                admin_body = (
                    f"Dear Admin,\n\nA new application has been submitted for Stall ID {stall_id} by {tenant_fullname}.\n"
                    f"Details:\n- Start Date: {start_date}\n- Duration: {duration} months\n- Reason: {reason}"
                )
                send_email_notification(admin_email, admin_subject, admin_body)

                # Insert notification for all admins
                notification_message = f"Dear Admin,\n\nA new application has been submitted for Stall ID {stall_id} by {tenant_fullname}."
                insert_notification_for_all_admins(notification_message)

            # Show confirmation messagebox after submission
            messagebox.showinfo("Stall Application", "Your application has been successfully submitted.")

            application_window.destroy()
            tenant_dashboard()

        def send_email_notification(to_email, subject, body):
            try:
                # Email configuration
                sender_email = "projectall2.2024@gmail.com"
                sender_password = "xiim atxo oajc mtly"

                # Set up the MIME
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = to_email
                msg['Subject'] = subject

                # Attach the body with the msg instance
                msg.attach(MIMEText(body, 'plain'))

                # Create a secure connection with the server and send the email
                server = smtplib.SMTP('smtp.gmail.com', 587)  # Example using Gmail SMTP
                server.starttls()
                server.login(sender_email, sender_password)
                text = msg.as_string()
                server.sendmail(sender_email, to_email, text)
                server.quit()

                print(f"Email sent to {to_email}")
            except Exception as e:
                print(f"Failed to send email: {e}")
                messagebox.showerror("Email Error", f"There was an error sending the email to {to_email}.")

        submit_button = ctk.CTkButton(application_form_frame, text="Submit", command=submit_application,
                                      fg_color='#007ACC', hover_color='#005F99', text_color='white',
                                      font=("Arial", 18, 'bold'))
        submit_button.grid(row=6, column=0, columnspan=3, pady=10)

        # Close button to close the application window
        close_button = ctk.CTkButton(application_form_frame, text="Close",
                                     command=lambda: (application_window.destroy(), tenant_dashboard()),
                                     fg_color='#FF4D4D', hover_color='#CC0000', text_color='white',
                                     font=("Arial", 18, 'bold'))
        close_button.grid(row=7, column=0, columnspan=3, pady=10)

        application_window.mainloop()

    def payment():
        for widget in content_frame.winfo_children():
            widget.destroy()

        # Create a frame to hold all the content
        payment_frame = Frame(content_frame, bd=2, relief="groove", bg="#C7D3FF", padx=10, pady=2)
        payment_frame.pack(fill="both", expand=True)

        title_label = Label(payment_frame, text="Payment", bg="#C7D3FF", font=("Bauhaus 93", 22, "bold"),
                            fg="black")
        title_label.pack(pady=0, anchor='center')

        # Connect to the database
        conn = sqlite3.connect('stall_rental_system.db')
        cursor = conn.cursor()

        # Fetch tenant info using username
        cursor.execute(""" 
            SELECT t.tenant_id, t.username, t.ic, s.stall_id, s.rent_price_per_month, r.rental_id, r.start_date, r.end_date 
            FROM tenant t 
            LEFT JOIN rental r ON t.tenant_id = r.tenant_id 
            LEFT JOIN stall s ON r.stall_id = s.stall_id 
            WHERE t.username = ?
        """, (logged_in_user['username'],))
        tenant_info = cursor.fetchone()

        if tenant_info:
            tenant_id, username, ic, stall_id, rent_price, rental_id, start_date, end_date = tenant_info

            # Display tenant info
            Label(payment_frame, text=f"Username: {username}", font=('Arial', 12, 'bold'), bg="#C7D3FF").pack(
                anchor='w',
                padx=20, pady=5)
            Label(payment_frame, text=f"IC: {ic}", font=('Arial', 12, 'bold'), bg="#C7D3FF").pack(anchor='w', padx=20,
                                                                                                  pady=5)

            # Initialize the Treeview table for displaying payment periods
            columns = ('Period', 'Amount (RM)', 'Status')
            payment_table = ttk.Treeview(payment_frame, columns=columns, show='headings', selectmode='browse')

            # Define headings (centered)
            payment_table.heading('Period', text='Period', anchor='center')
            payment_table.heading('Amount (RM)', text='Amount (RM)', anchor='center')
            payment_table.heading('Status', text='Status', anchor='center')

            # Define columns (centered)
            payment_table.column('Period', anchor='center', width=200)
            payment_table.column('Amount (RM)', anchor='center', width=100)
            payment_table.column('Status', anchor='center', width=100)

            if stall_id is not None:
                # Convert the start_date and end_date from strings to datetime objects
                start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

                # Display the stall and rental info
                Label(payment_frame, text=f"Stall ID: {stall_id}", font=('Arial', 12, 'bold'), bg="#C7D3FF").pack(
                    anchor='w',
                    padx=20,
                    pady=5)
                Label(payment_frame,
                      text=f"Rental Period: {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}",
                      font=('Arial', 12, 'bold'), bg="#C7D3FF").pack(anchor='w', padx=20, pady=5)
                Label(payment_frame, text=f"Rent Price (per month): RM{rent_price}", font=('Arial', 12, 'bold'),
                      bg="#C7D3FF").pack(anchor='w', padx=20, pady=5)

                # Fetch existing unpaid periods for this tenant
                cursor.execute(""" 
                    SELECT paid_periods 
                    FROM payment 
                    WHERE tenant_id = ? AND payment_status = 'unpaid' 
                """, (tenant_id,))
                unpaid_periods = cursor.fetchall()

                # Insert unpaid periods into the table
                if unpaid_periods:
                    for i, (period_label,) in enumerate(unpaid_periods):
                        status = 'unpaid' if i == 0 else 'Not Available'  # Only the first period is unpaid
                        payment_table.insert('', 'end', values=(period_label, rent_price, status))
                else:
                    # Insert a row indicating no unpaid rental periods
                    payment_table.insert('', 'end', values=("No unpaid rental periods", "N/A", "N/A"))

            else:
                # Display 'None' for stall and rental info if no stall is assigned
                Label(payment_frame, text="Stall ID: None", font=('Arial', 12, 'bold'), bg="#C7D3FF").pack(anchor='w',
                                                                                                           padx=20,
                                                                                                           pady=5)
                Label(payment_frame, text="Rental Period: None", font=('Arial', 12, 'bold'), bg="#C7D3FF").pack(
                    anchor='w',
                    padx=20, pady=5)
                Label(payment_frame, text="Rent Price (per month): None", font=('Arial', 12, 'bold'),
                      bg="#C7D3FF").pack(
                    anchor='w', padx=20, pady=5)

                # Insert a row indicating no stall is assigned
                payment_table.insert('', 'end', values=("No stall assigned", "N/A", "N/A"))

            # Pack the Treeview at the bottom of the frame
            payment_table.pack(fill="both", expand=True)

            # Pay button
            def create_gradient(canvas, color1, color2):
                width = 1920
                height = 1080
                limit = 100  # Determines the smoothness of the gradient

                for i in range(limit):
                    color = f"#{int((1 - i / limit) * int(color1[1:3], 16) + (i / limit) * int(color2[1:3], 16)):02x}" \
                            f"{int((1 - i / limit) * int(color1[3:5], 16) + (i / limit) * int(color2[3:5], 16)):02x}" \
                            f"{int((1 - i / limit) * int(color1[5:7], 16) + (i / limit) * int(color2[5:7], 16)):02x}"
                    canvas.create_rectangle(0, i * (height / limit), width, (i + 1) * (height / limit), outline="",
                                            fill=color)

            def pay_selected_period():
                global payment_type_window
                selected_item = payment_table.selection()
                if not selected_item:
                    messagebox.showwarning("Selection Error", "Please select a period to pay.")
                    return

                selected_period = payment_table.item(selected_item)['values'][0]
                status = payment_table.item(selected_item)['values'][2]

                if status == 'Not Available':
                    messagebox.showwarning("Payment Error",
                                           "You cannot pay for future periods without paying for the current period.")
                elif status == 'paid':
                    messagebox.showwarning("Payment Error", "This period has already been paid.")
                elif selected_period == "No unpaid rental periods":
                    messagebox.showwarning("Payment Error", "There are no unpaid rental periods.")
                else:
                    # Open payment type selection window
                    payment_type_window = Toplevel()
                    payment_type_window.title("Select Payment Type")
                    payment_type_window.geometry("300x250")

                    # Canvas for gradient background
                    canvas = Canvas(payment_type_window, width=1920, height=1080, highlightthickness=0)
                    canvas.pack(fill="both", expand=True)
                    create_gradient(canvas, "#C7D3FF", "#4A78B1")

                    # Frame to center widgets and add spacing
                    frame = ctk.CTkFrame(payment_type_window, fg_color="transparent", border_width=2,
                                         border_color="#2F4F6F")
                    frame.place(relx=0.5, rely=0.5, anchor="center")

                    # Header label
                    ctk.CTkLabel(frame, text="Choose Payment Type", font=('Arial', 16, 'bold')).pack(pady=10, padx=10)

                    # Radio button options for payment types
                    payment_type_var = StringVar(value="Credit Card")  # Default option
                    ctk.CTkRadioButton(frame, text="Credit Card", variable=payment_type_var, value="Credit Card",
                                       font=('Arial', 14, 'bold')).pack(anchor="w", pady=5, padx=10)
                    ctk.CTkRadioButton(frame, text="Bank Transfer", variable=payment_type_var, value="Bank Transfer",
                                       font=('Arial', 14, 'bold')).pack(anchor="w", pady=5, padx=10)
                    ctk.CTkRadioButton(frame, text="Touch n Go", variable=payment_type_var, value="Touch n Go",
                                       font=('Arial', 14, 'bold')).pack(anchor="w", pady=5, padx=10)

                    # Confirm button
                    ctk.CTkButton(frame, text="Confirm Payment", font=('Arial', 16, 'bold'),
                                  command=lambda: finalize_payment(selected_period, tenant_id, rent_price, rental_id,
                                                                   payment_type_var.get())).pack(pady=20, padx=10)

            def finalize_payment(period, tenant_id, rent_price, rental_id, payment_type):
                # Close the payment type selection window
                payment_type_window.destroy()

                # Proceed with payment processing and save the selected payment type
                process_payment(period, tenant_id, rent_price, rental_id, payment_type)

            pay_button = ctk.CTkButton(payment_frame, text="Pay Selected Period", command=pay_selected_period,
                                       font=('times new roman', 22, 'bold'),
                                       fg_color='#00699E',
                                       text_color='white', corner_radius=50)
            pay_button.bind("<Enter>", lambda e: pay_button.configure(fg_color="#0085C7"))
            pay_button.bind("<Leave>", lambda e: pay_button.configure(fg_color="#00699E"))

            if stall_id is None:
                pay_button.configure(state=DISABLED)  # Disable button if no stall

                def twinkle():
                    # Alternate between showing and hiding the message
                    current_color = twinkle_label.cget("fg")
                    next_color = "#FF0000" if current_color == "#C7D3FF" else "#C7D3FF"
                    twinkle_label.configure(fg=next_color)
                    payment_frame.after(500, twinkle)

                # Add a twinkling message at the bottom of the Treeview
                twinkle_label = Label(payment_frame, text="No stall assigned. Please contact the admin.",
                                      font=('Arial', 10), fg="#FF0000", bg="#C7D3FF")
                twinkle_label.pack(pady=10)
                twinkle()  # Start the twinkling animation
            else:
                pay_button.pack(pady=20)

            # Button to view payment history
            def view_payment_history():
                # Close the current database connection and open a new one
                conn = sqlite3.connect('stall_rental_system.db')
                cursor = conn.cursor()

                # Create a new frame for payment history
                history_frame = Frame(content_frame, bd=2, relief="groove", bg="#C7D3FF", padx=10, pady=10)
                history_frame.pack(fill="both", expand=True)

                # Payment History Title
                Label(history_frame, text="Payment History", font=("Bauhaus 93", 22, 'bold'), bg="#C7D3FF").pack(
                    anchor='w', padx=20,
                    pady=5)

                # Initialize the Treeview for displaying payment history
                history_columns = ('Period', 'Amount (RM)', 'Status', 'Date')
                history_table = ttk.Treeview(history_frame, columns=history_columns, show='headings',
                                             selectmode='browse')

                # Define headings
                for col in history_columns:
                    history_table.heading(col, text=col, anchor='center')
                    history_table.column(col, anchor='center', width=100)

                # Fetch payment history from the database
                cursor.execute(""" 
                    SELECT paid_periods, amount, payment_status, payment_date 
                    FROM payment 
                    WHERE tenant_id = ? 
                    ORDER BY payment_date DESC
                """, (tenant_id,))
                payment_history = cursor.fetchall()

                # Insert payment history into the Treeview
                if payment_history:
                    for period_label, amount, status, payment_date in payment_history:
                        history_table.insert('', 'end', values=(period_label, amount, status, payment_date))
                else:
                    history_table.insert('', 'end', values=("No payment history available", "", "", ""))

                history_table.pack(fill="both", expand=True)

                # Back button to return to payment frame
                def back_to_payment():
                    history_frame.destroy()
                    payment()  # Call the payment function again to reinitialize the payment frame

                back_button = ctk.CTkButton(history_frame, text="Back to Payment", command=back_to_payment,
                                            fg_color="#00699E", hover_color="#0085C7")
                back_button.pack(pady=20)

            def ToggleToHistory(event=None):
                if payment_frame is not None:
                    payment_frame.destroy()
                view_payment_history()

            view_history_button = Label(payment_frame, text="View Payment History", fg="blue", font=('arial', 10),
                                        bg="#C7D3FF")
            view_history_button.bind('<Enter>',
                                     lambda event, label=view_history_button: label.configure(
                                         font=('arial', 10, 'underline')))
            view_history_button.bind('<Leave>',
                                     lambda event, label=view_history_button: label.configure(font=('arial', 10)))
            view_history_button.bind('<Button-1>', ToggleToHistory)
            view_history_button.pack(pady=20)

        conn.close()

    def process_payment(period, tenant_id, rent_price, rental_id, payment_type):
        conn = sqlite3.connect('stall_rental_system.db')
        cursor = conn.cursor()

        # Record the current time as payment date
        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Check if the period has already been paid (to handle edge cases)
        cursor.execute("""
            SELECT payment_status 
            FROM payment
            WHERE tenant_id = ? AND paid_periods = ?
        """, (tenant_id, period))
        payment_status = cursor.fetchone()

        if payment_status and payment_status[0] == 'paid':
            messagebox.showerror("Payment Error", f"The period {period} has already been paid.")
        else:
            # Proceed with the payment process and mark the period as 'Paid'
            cursor.execute("""
                UPDATE payment
                SET payment_date = ?, amount = ?, payment_status = 'paid', payment_type = ?
                WHERE tenant_id = ? AND rental_id = ? AND paid_periods = ?
            """, (current_time, rent_price, payment_type, tenant_id, rental_id, period))

            conn.commit()

            messagebox.showinfo("Payment", f"Payment for {period} processed successfully with {payment_type}!")

            # Generate receipt after processing the payment
            generate_receipt(tenant_id, period)

            # Refresh the payment screen to show updated status
            payment()

            # Get tenant's email and full name for sending the receipt via email
            cursor.execute("SELECT email_address, fullname FROM tenant WHERE tenant_id = ?", (tenant_id,))
            tenant_info = cursor.fetchone()

            if tenant_info:
                tenant_email, fullname = tenant_info

                # Send email with receipt to tenant and admin
                admin_email = 'projectall2.2024@gmail.com'  # Use the same admin email for all admins
                pdf_filename = f"Receipt_{fullname}_Period_{period}.pdf"  # Use full name in the filename
                send_email_with_receipt(tenant_email, admin_email, pdf_filename, fullname)

                # Insert notifications for the tenant and all admins
                insert_notification("tenant", tenant_id,
                                    f"Dear Tenant,\n\nYou have made a payment for the period: {period}\n\n\nBest regards,\nGovernment Stall Rental System")
                insert_notification_for_all_admins(
                    f"Dear Admin,\n\n{fullname} has made a payment for the period: {period}")

        conn.close()

    def notification():
        """
        Displays notifications for the currently logged-in user. Tenants can view their own notifications,
        while admins can view all notifications. When a row is selected in the Treeview, it shows the message details beside the Treeview.
        """
        # Clear existing widgets
        for widget in content_frame.winfo_children():
            widget.destroy()

        notification_frame = Frame(content_frame, bg="#C7D3FF", padx=20, pady=10, bd=2, relief='groove')
        notification_frame.pack(fill='both', expand=True)

        ctk.CTkLabel(notification_frame, text="Notifications", font=("Bauhaus 93", 24)).pack(pady=10)

        # Create a frame to hold both the Treeview and the message display
        notification_content_frame = ctk.CTkFrame(notification_frame, width=500, height=300, fg_color="#C7D3FF")
        notification_content_frame.pack(fill='both', expand=False)
        notification_content_frame.pack_propagate(False)

        # Create a frame to hold both the Treeview and the scrollbar together
        table_frame = ctk.CTkFrame(notification_content_frame)
        table_frame.pack(side='left', fill='both', expand=True)

        # Create a Treeview widget to display notifications
        notification_table = ttk.Treeview(table_frame, columns=("Date",), show='headings', height=20)
        notification_table.pack(side='left', fill='both', expand=True)

        # Define the column heading and width for the "Date" column
        notification_table.heading("Date", text="Date")
        notification_table.column("Date", width=150)

        # Create a scrollbar for the Treeview and pack it to the right of the Treeview
        scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=notification_table.yview)
        scrollbar.pack(side='right', fill='y')
        notification_table.configure(yscrollcommand=scrollbar.set)

        # Create a CTkTextbox widget to display the selected message
        message_display = ctk.CTkTextbox(notification_content_frame, height=20, wrap="word", state="disabled")
        message_display.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        def on_row_select(event):
            # Get the selected item
            selected_item = notification_table.selection()
            if selected_item:
                item_values = notification_table.item(selected_item, 'values')
                notification_id = notification_table.item(selected_item, 'tags')[0]
                if item_values:
                    selected_date = item_values[0]

                    # Fetch the full message corresponding to the selected notification_id
                    cursor.execute("""
                            SELECT message FROM notification 
                            WHERE notification_id = ?
                        """, (notification_id,))
                    message = cursor.fetchone()

                    if message:
                        selected_message = message[0]
                        message_display.configure(state="normal")
                        message_display.delete("1.0", END)
                        message_display.insert("1.0", selected_message)
                        message_display.configure(state="disabled")

        # Bind the row selection event to the Treeview
        notification_table.bind("<<TreeviewSelect>>", on_row_select)

        # Flag to track if the "No notifications" message has been displayed
        message_displayed = False
        no_notifications_label = None

        def twinkle_label():
            """Function to create a twinkling effect on the no_notifications_label."""
            if no_notifications_label:
                current_color = no_notifications_label.cget("text_color")
                new_color = "#FF0000" if current_color == "#C7D3FF" else "#C7D3FF"
                no_notifications_label.configure(text_color=new_color)
                no_notifications_label.after(500, twinkle_label)

        def load_notifications(show_history=False):
            nonlocal message_displayed, no_notifications_label
            notification_table.delete(*notification_table.get_children())

            message_display.configure(state="normal")
            message_display.delete("1.0", END)
            message_display.configure(state="disabled")

            if no_notifications_label:
                no_notifications_label.destroy()
                no_notifications_label = None

            try:
                username = logged_in_user.get("username")

                cursor.execute("SELECT tenant_id FROM tenant WHERE username = ?", (username,))
                tenant = cursor.fetchone()

                if tenant:
                    tenant_id = tenant[0]
                    if show_history:
                        cursor.execute(""" 
                                SELECT notification_id, notification_date FROM notification 
                                WHERE recipient = 'tenant' AND recipient_id = ? AND is_read = 1
                                ORDER BY notification_date DESC
                            """, (tenant_id,))
                    else:
                        cursor.execute("""
                                SELECT notification_id, notification_date FROM notification 
                                WHERE recipient = 'tenant' AND recipient_id = ? AND is_read = 0
                                ORDER BY notification_date DESC
                            """, (tenant_id,))

                    notifications = cursor.fetchall()

                    if not show_history:
                        cursor.execute(""" 
                                UPDATE notification
                                SET is_read = 1
                                WHERE recipient = 'tenant' AND recipient_id = ?
                            """, (tenant_id,))

                else:
                    cursor.execute("SELECT admin_id FROM admin WHERE username = ?", (username,))
                    admin = cursor.fetchone()

                    if admin:
                        admin_id = admin[0]
                        if show_history:
                            cursor.execute(""" 
                                    SELECT notification_id, notification_date FROM notification 
                                    WHERE recipient = 'admin' AND recipient_id = ? AND is_read = 1
                                    ORDER BY notification_date DESC
                                """, (admin_id,))
                        else:
                            cursor.execute("""
                                    SELECT notification_id, notification_date FROM notification 
                                    WHERE recipient = 'admin' AND recipient_id = ? AND is_read = 0
                                    ORDER BY notification_date DESC
                                """, (admin_id,))

                        notifications = cursor.fetchall()

                        if not show_history:
                            cursor.execute(""" 
                                    UPDATE notification
                                    SET is_read = 1
                                    WHERE recipient = 'admin' AND recipient_id = ?
                                """, (admin_id,))

                    else:
                        ctk.CTkLabel(notification_frame, text="User not found.", font=("Arial", 14)).pack(pady=10)
                        return

                conn.commit()
                message_displayed = False

                if notifications:
                    for notification_id, notification_date in notifications:
                        notification_table.insert("", "end", values=(notification_date,), tags=(notification_id,))
                else:
                    if not message_displayed:
                        no_notifications_label = ctk.CTkLabel(notification_frame, text="No notifications available.",
                                                              font=("Arial", 18), text_color="#FF0000")
                        no_notifications_label.pack(pady=10)
                        message_displayed = True
                        twinkle_label()

            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Error retrieving notifications: {e}")

        show_history_var = ctk.BooleanVar(value=False)
        toggle_button = ctk.CTkCheckBox(notification_frame, text="Show Read Notifications", variable=show_history_var,
                                        font=("Arial", 12), command=lambda: load_notifications(show_history_var.get()))
        toggle_button.pack(pady=10)

        load_notifications(show_history=False)

    def feedback():
        for widget in content_frame.winfo_children():
            widget.destroy()

        def submit_feedback():
            tenant_feedback = feedback_text.get("1.0", END)
            tenant_id = fetch_tenant_id(logged_in_user['username'], logged_in_user['password'])

            if tenant_feedback.strip() == "":
                messagebox.showerror("Error", "Feedback cannot be empty!")
                return

            conn = sqlite3.connect("stall_rental_system.db")
            cursor = conn.cursor()

            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("INSERT INTO feedback (tenant_id, feedback,feedback_date) VALUES (?, ?,?)",
                           (tenant_id, tenant_feedback, current_time))
            conn.commit()

            messagebox.showinfo("Success", "Feedback submitted successfully!")
            feedback_text.delete("1.0", END)
            load_feedback(tenant_id)

        def load_feedback(tenant_id, sort_order='desc', selected_date=None):
            feedback_text_box.config(state=NORMAL)
            feedback_text_box.delete("1.0", END)
            conn = sqlite3.connect("stall_rental_system.db")
            cursor = conn.cursor()

            query = "SELECT feedback, response, feedback_date, response_date FROM feedback WHERE tenant_id = ?"
            params = [tenant_id]

            if selected_date and selected_date != "Select All":
                query += " AND DATE(feedback_date) = ?"
                params.append(selected_date)

            query += f" ORDER BY feedback_date {sort_order}"
            cursor.execute(query, params)
            feedback_data = cursor.fetchall()

            feedback_text_box.tag_configure("feedback", font=("Arial", 10), foreground="black")
            feedback_text_box.tag_configure("response", font=("Arial", 10), foreground="green")
            feedback_text_box.tag_configure("date", font=("Arial", 8), foreground="blue")

            separator = "\n" + "-" * 66 + "\n"

            for feedback_item in feedback_data:
                feedback_text = f"Feedback:\n{feedback_item[0]}\n\n"
                response_text = f"Response From Admin:\n{feedback_item[1] or 'No response yet'}\n\n"
                feedback_date_text = f"Feedback Date: {feedback_item[2]}\n"
                response_date_text = f"Response Date: {feedback_item[3] or 'N/A'}\n"

                feedback_text_box.insert(END, feedback_text, "feedback")
                feedback_text_box.insert(END, response_text, "response")
                feedback_text_box.insert(END, feedback_date_text, "date")
                feedback_text_box.insert(END, response_date_text, "date")
                feedback_text_box.insert(END, separator)

            conn.close()
            feedback_text_box.config(state=DISABLED)

        def load_feedback_dates():
            conn = sqlite3.connect("stall_rental_system.db")
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT DATE(feedback_date) FROM feedback WHERE tenant_id = ?", (tenant_id,))
            dates = [row[0] for row in cursor.fetchall()]
            conn.close()
            return dates

        def apply_filters():
            selected_date = date_combobox.get()
            sort_order = sort_var.get()
            load_feedback(tenant_id, sort_order, selected_date)

        tenant_id = fetch_tenant_id(logged_in_user['username'], logged_in_user['password'])

        feedback_frame = Frame(content_frame, bg="#C7D3FF", padx=20, pady=10, bd=2, relief='groove')
        feedback_frame.pack(fill='both', expand=True)

        fd_center_frame = Frame(feedback_frame, bg="#C7D3FF")
        fd_center_frame.pack(anchor='center')

        form_frame = ctk.CTkFrame(fd_center_frame, fg_color="#D9D9D9", border_color="#A8A8A8", border_width=2)
        form_frame.pack(side='left', padx=10, fill='y')

        Label(form_frame, text="Feedback:", font=('Algerian', 16, 'bold'), bg="#D9D9D9").pack(pady=10)

        feedback_text = Text(form_frame, height=20, width=50, highlightbackground="black", highlightcolor="black",
                             highlightthickness=2)
        feedback_text.pack(pady=10, padx=30)

        submit_button = ctk.CTkButton(form_frame, text="Submit Feedback", command=submit_feedback,
                                      font=('Arial', 20, 'bold'), fg_color='#00527B', text_color='white',
                                      corner_radius=50)
        submit_button.bind("<Enter>", lambda e: submit_button.configure(fg_color="#0077B3"))
        submit_button.bind("<Leave>", lambda e: submit_button.configure(fg_color="#00527B"))
        submit_button.pack(pady=10)

        history_frame = ctk.CTkFrame(fd_center_frame, fg_color="#D9D9D9", border_color="#A8A8A8", border_width=2)
        history_frame.pack(side='left', padx=10, fill='y')

        Label(history_frame, text="Feedback History:", font=('Algerian', 16, 'bold'), bg="#D9D9D9").pack(pady=10)

        # Create a frame for filters at the bottom
        filter_frame = Frame(history_frame, bg="#C4C4C4")
        filter_frame.pack(side='bottom', pady=10, padx=10)

        sort_var = StringVar(value='desc')
        ctk.CTkRadioButton(filter_frame, text="New to Old", variable=sort_var, value='desc',
                           command=apply_filters).pack(side='left', padx=5)
        ctk.CTkRadioButton(filter_frame, text="Old to New", variable=sort_var, value='asc', command=apply_filters).pack(
            side='left', padx=5)

        # Date selection
        Label(filter_frame, text="Select Date:", bg="#C4C4C4").pack(side='left', padx=5)
        date_combobox = ctk.CTkComboBox(filter_frame, values=["Select All"] + load_feedback_dates())
        date_combobox.set("Select All")
        date_combobox.pack(side='left', padx=5)

        filter_button = ctk.CTkButton(filter_frame, text="Apply Filters", command=apply_filters,
                                      font=('Arial', 16, 'bold'), fg_color='#00527B', text_color='white',
                                      corner_radius=50)
        filter_button.bind("<Enter>", lambda e: filter_button.configure(fg_color="#0077B3"))
        filter_button.bind("<Leave>", lambda e: filter_button.configure(fg_color="#00527B"))
        filter_button.pack(side='left', padx=5)

        text_frame = Frame(history_frame, bg="#D9D9D9")
        text_frame.pack(fill='both', expand=True, pady=10, padx=30)

        feedback_text_box = Text(text_frame, height=20, width=50, wrap="word", highlightbackground="black",
                                 highlightcolor="black", highlightthickness=2)
        feedback_text_box.pack(side='left', fill='both', expand=True)

        scrollbar = Scrollbar(text_frame, command=feedback_text_box.yview)
        scrollbar.pack(side='right', fill='y')

        feedback_text_box.config(yscrollcommand=scrollbar.set)

        load_feedback(tenant_id)

    def profiles():
        for widget in content_frame.winfo_children():
            widget.destroy()

        profiles_frame = Frame(content_frame, bg="#C7D3FF", padx=20, bd=2, relief='groove')
        profiles_frame.pack(fill='both', expand=True)

        title_label = Label(profiles_frame, text="Tenant Profiles", bg="#C7D3FF", font=("Bauhaus 93", 24, "bold"),
                            fg="black")
        title_label.pack(pady=10, anchor='center')

        # Assuming logged_in_user has the tenant's username
        username = logged_in_user.get('username')

        if username:
            # Retrieve tenant information from the database
            cursor.execute("SELECT * FROM tenant WHERE username = ?", (username,))
            tenant_info = cursor.fetchone()

            if tenant_info:
                tenant_id, username, password, fullname, ic, date_of_birth, email_address, phone_number, face_id_image, face_embedding = tenant_info

                # Create a frame for holding the image and info side by side, centered
                main_frame = ctk.CTkFrame(profiles_frame, fg_color="#CFCFCF", border_color="#A8A8A8", border_width=2)
                main_frame.pack(pady=20, anchor='center')

                # Create a frame for the face image
                face_frame = Frame(main_frame, bg="#CFCFCF")
                face_frame.pack(side='left', padx=20, pady=20)

                face_image_label = Label(face_frame, bg="#CFCFCF")
                face_image_label.pack()

                if face_id_image:
                    try:
                        # Open the face ID image
                        img = Image.open(face_id_image)
                        img = img.resize((280, 280), Image.Resampling.LANCZOS)  # Resize as needed
                        face_image = ImageTk.PhotoImage(img)

                        face_image_label.config(image=face_image)
                        face_image_label.image = face_image  # Keep a reference to avoid garbage collection

                    except Exception as e:
                        print(f"Error loading image: {e}")
                        face_image_label.config(text="Face ID image not found.", bg="#C7D3FF")

                # Create a frame for tenant information
                info_frame = ctk.CTkFrame(main_frame, fg_color="#CFCFCF", border_color="#A8A8A8", border_width=2)
                info_frame.pack(side='left', padx=20)

                # Display tenant information with labels and values beside each other
                def add_info_row(label_text, value_text):
                    row_frame = Frame(info_frame, bg="#CFCFCF")
                    row_frame.pack(anchor='w', padx=20,pady=5)
                    Label(row_frame, text=label_text, bg="#CFCFCF", font=("Arial", 12, 'bold')).pack(side='left')
                    Label(row_frame, text=value_text, bg="#CFCFCF", fg="blue", font=("Arial", 12)).pack(side='left')

                add_info_row("Username: ", username)
                add_info_row("Full Name: ", fullname)
                add_info_row("IC: ", ic)
                add_info_row("Date of Birth: ", str(date_of_birth))
                add_info_row("Email: ", email_address)
                add_info_row("Phone Number: ", phone_number)

                # Add the edit button below the main frame
                edit_button = ctk.CTkButton(profiles_frame, text="edit information", font=("Arial", 20, "bold"),
                                            fg_color='#00527B', hover_color="#0085C7", text_color='white',
                                            corner_radius=50, command=open_edit_user_info_and_close_dashboard)
                edit_button.pack(pady=10, anchor='center')

            else:
                Label(profiles_frame, text="Tenant not found.", bg="#C7D3FF", font=("Arial", 12)).pack(pady=10)
        else:
            Label(profiles_frame, text="No user is logged in.", bg="#C7D3FF", font=("Arial", 12)).pack(pady=10)

    def edit_user_info():
        global password_entry, eye_button, eye_open_image, eye_closed_image

        # Function to fetch tenant ID based on username and password
        def fetch_tenant_id(username, password):
            conn = sqlite3.connect("stall_rental_system.db")
            cursor = conn.cursor()

            try:
                # Fetch the tenant ID based on the stored username and password
                query = """
                        SELECT tenant_id
                        FROM tenant
                        WHERE username = ? AND password = ?
                        """
                cursor.execute(query, (username, password))
                tenant_data = cursor.fetchone()

                if not tenant_data:
                    raise sqlite3.Error("Tenant not found")

                tenant_id = tenant_data[0]  # Extract tenant_id from the fetched data

                return tenant_id

            except sqlite3.Error as e:
                print(f"SQLite error: {e}")
                return None

        # Function to fetch tenant data from the database
        def fetch_tenant_data(tenant_id):
            conn = sqlite3.connect("stall_rental_system.db")
            cursor = conn.cursor()

            # Fetch tenant data
            cursor.execute("SELECT username, email_address, phone_number, password FROM tenant WHERE tenant_id = ?",
                           (tenant_id,))
            tenant_data = cursor.fetchone()

            return tenant_data

        # Function to update tenant data in the database
        def update_tenant_data(tenant_id, new_username, new_email_address, new_phone_number, new_password):
            conn = sqlite3.connect("stall_rental_system.db")
            cursor = conn.cursor()

            try:
                # Check if the new username is already in use by another tenant
                cursor.execute("SELECT tenant_id FROM tenant WHERE username = ? AND tenant_id != ?",
                               (new_username, tenant_id))
                existing_tenant = cursor.fetchone()

                if existing_tenant:
                    messagebox.showerror("Username Error",
                                         "Username already exists. Please choose a different username.")
                    return False

                # Update tenant data
                cursor.execute(
                    "UPDATE tenant SET username = ?, email_address = ?, phone_number = ?, password = ? WHERE tenant_id = ?",
                    (new_username, new_email_address, new_phone_number, new_password, tenant_id)
                )
                conn.commit()

                # Update logged_in_user
                logged_in_user['username'] = new_username
                logged_in_user['password'] = new_password

                return True

            except sqlite3.Error as e:
                print(f"SQLite error: {e}")
                return False

        # Function to load tenant data into labels and allow editing
        def load_tenant_data_view(tenant_id):
            tenant_data = fetch_tenant_data(tenant_id)
            if tenant_data:
                username_var.set(tenant_data[0])
                email_address_var.set(tenant_data[1])
                phone_number_var.set(tenant_data[2])
                password_var.set(tenant_data[3])

        # Function to save tenant data
        def save_tenant_data(tenant_id):
            username = username_var.get()
            email_address = email_address_var.get()
            phone_number = phone_number_var.get()
            password = password_var.get()

            if update_tenant_data(tenant_id, username, email_address, phone_number, password):
                load_tenant_data_view(tenant_id)
                messagebox.showinfo("Success", "Tenant information updated successfully!")
            else:
                load_tenant_data_view(tenant_id)

        # Function to toggle between edit and save modes
        def toggle_edit_save():
            nonlocal is_edit_mode
            if is_edit_mode:
                # Save the data and disable entries
                save_tenant_data(tenant_id)
                toggle_entry_state(DISABLED)
                edit_save_button.config(text="Edit")
            else:
                # Enable the entries for editing
                toggle_entry_state(NORMAL)
                edit_save_button.config(text="Save")

            is_edit_mode = not is_edit_mode

        # Function to toggle the state of entry fields
        def toggle_entry_state(state):
            username_entry.config(state=state)
            email_address_entry.config(state=state)
            phone_number_entry.config(state=state)
            password_entry.config(state=state)

        def close_edit_window():
            edit_window.destroy()
            tenant_dashboard()

        # Create and display the user info edit window
        tenant_id = fetch_tenant_id(logged_in_user['username'], logged_in_user['password'])

        if tenant_id:
            edit_window = Toplevel()
            edit_window.title("Tenant Information")
            edit_window.geometry("1920x1080+0+0")  # window size and position
            edit_window.state("zoomed")

            # Load the background image
            image = Image.open("image\\bg2.png").convert("RGBA")
            resized_image = image.resize((1920, 1080), Image.Resampling.LANCZOS)

            # Adjust transparency
            alpha = 180  # Transparency level (0 is fully transparent, 255 is fully opaque)
            alpha_channel = resized_image.split()[3].point(lambda p: p * alpha / 255.)
            transparent_image = Image.merge("RGBA", (resized_image.split()[:3] + (alpha_channel,)))

            # Convert the image to a format tkinter can handle
            bg2_image = ImageTk.PhotoImage(transparent_image)

            # Create a canvas to hold the image and text
            canvas = Canvas(edit_window, width=1920, height=1080)
            canvas.place(x=0, y=0, relwidth=1, relheight=1)

            # Place the background image on the canvas
            canvas.create_image(0, 0, anchor='nw', image=bg2_image)

            is_edit_mode = False  # Toggle edit/save mode

            # Create entry variables
            username_var = StringVar()
            email_address_var = StringVar()
            phone_number_var = StringVar()
            password_var = StringVar()

            # Load tenant data into the entry variables
            load_tenant_data_view(tenant_id)

            # Create and pack the title label on the canvas
            canvas.create_text(770, 50, text="Tenant Information", font=('Algerian', 26, 'bold'), fill="black")

            # Create labels and entry fields on the canvas
            canvas.create_text(620, 150, text="Username:", font=('Arial', 16, 'bold'), fill="black")
            username_entry = Entry(edit_window, textvariable=username_var, font=('Arial', 16),
                                   highlightbackground="black", highlightcolor="black", highlightthickness=2)
            canvas.create_window(870, 150, window=username_entry, width=300)

            canvas.create_text(620, 220, text="Email Address:", font=('Arial', 16, 'bold'), fill="black")
            email_address_entry = Entry(edit_window, textvariable=email_address_var, font=('Arial', 16),
                                        highlightbackground="black", highlightcolor="black", highlightthickness=2)
            canvas.create_window(870, 220, window=email_address_entry, width=300)

            canvas.create_text(620, 290, text="Phone Number:", font=('Arial', 16, 'bold'), fill="black")
            phone_number_entry = Entry(edit_window, textvariable=phone_number_var, font=('Arial', 16),
                                       highlightbackground="black", highlightcolor="black", highlightthickness=2)
            canvas.create_window(870, 290, window=phone_number_entry, width=300)

            canvas.create_text(620, 360, text="Password:", font=('Arial', 16, 'bold'), fill="black")
            password_entry = Entry(edit_window, textvariable=password_var, show='*', font=('Arial', 16),
                                   highlightbackground="black", highlightcolor="black", highlightthickness=2)
            canvas.create_window(870, 360, window=password_entry, width=300)

            eye_open_image = ImageTk.PhotoImage(Image.open("image\\open_eye.png").resize((25, 25)))
            eye_closed_image = ImageTk.PhotoImage(Image.open("image\\closed_eye.png").resize((25, 25)))

            # Create and place the eye button
            eye_button = Button(edit_window, image=eye_closed_image, command=toggle_password_visibility, bg='white',
                                borderwidth=0)
            canvas.create_window(1002, 360, window=eye_button, width=30)

            # Create and place the Edit/Save button
            edit_save_button = Button(edit_window, text="Edit", command=toggle_edit_save, font=('Arial', 16, 'bold'),
                                      bg='#8EDE7E', fg='white')
            edit_save_button.bind("<Enter>", lambda e: edit_save_button.configure(bg="#98ED86"))
            edit_save_button.bind("<Leave>", lambda e: edit_save_button.configure(bg="#8EDE7E"))
            canvas.create_window(770, 450, window=edit_save_button, width=150)

            # Create and place the Close button
            close_button = Button(edit_window, text="Close", command=close_edit_window, font=('Arial', 16, 'bold'),
                                  bg='#E3807D', fg='white')
            close_button.bind("<Enter>", lambda e: close_button.configure(bg="#F28885"))
            close_button.bind("<Leave>", lambda e: close_button.configure(bg="#E3807D"))
            canvas.create_window(770, 510, window=close_button, width=150)

            # Initially disable the entry fields
            toggle_entry_state(DISABLED)
            edit_window.image = bg2_image

    def toggle_password_visibility():
        """Toggle password visibility."""
        if password_entry.cget('show') == '*':
            password_entry.config(show='')
            eye_button.config(image=eye_open_image)
        else:
            password_entry.config(show='*')
            eye_button.config(image=eye_closed_image)

    def logout():
        result = messagebox.askquestion('System', 'Are you sure you want to logout?', icon="warning")
        if result == 'yes':
            MenuFrame.destroy()
            form_frame.deiconify()

    def open_edit_user_info_and_close_dashboard(event=None):
        MenuFrame.destroy()
        edit_user_info()

    # Function to update the selected category
    def update_selected_category(category):
        selected_category.set(category)
        top_canvas.itemconfig(selected_category_text_id, text=selected_category.get())

        # Call the appropriate function based on the selected category
        if category == "Stall":
            stall()
        elif category == "Apply Stall":
            apply_stall()
        elif category == "Payment":
            payment()
        elif category == "Notification":
            notification()
        elif category == "Feedback":
            feedback()
        elif category == "Profiles":
            profiles()

    # Function to toggle visibility of categories
    def toggle_categories():
        if category_frame.winfo_viewable():
            category_frame.pack_forget()  # Hide the category frame
            toggle_category_btn.configure(image=open_icon)  # Change button icon
            content_frame.pack(side='right', fill='both', expand=True)  # Expand content frame
            create_collapsed_icons()  # Display the collapsed icons beside the content_frame
        else:
            collapsed_icon_frame.pack_forget()  # Hide the collapsed icon frame
            category_frame.pack(side='left', fill='y')  # Show the full category frame
            toggle_category_btn.configure(image=close_icon)  # Change button icon
            content_frame.pack(side='right', fill='both', expand=True)  # Adjust content frame position

    # Function to create collapsed icons
    def create_collapsed_icons():
        for widget in collapsed_icon_frame.winfo_children():
            widget.destroy()

        # Create toggle button for collapsed icons
        toggle_category_btn = Button(collapsed_icon_frame, image=open_icon, command=toggle_categories, bg='black',
                                     borderwidth=0)
        toggle_category_btn.pack(side='top', pady=10)

        # Determine current theme to set colors
        current_bg = MenuFrame.cget('bg')
        icon_bg_color = "#C3C3C3" if current_bg == "#f8f8f8" else "#696969"

        for index, category in enumerate(categories):
            # Create category icon labels with appropriate background color
            category_icon_label = Label(collapsed_icon_frame, image=category_icons[category], bg=icon_bg_color)
            category_icon_label.pack(side='top', padx=10, pady=10)
            category_icon_label.bind("<Button-1>", lambda event, c=category: update_selected_category(c))

        # Create logout icon label with appropriate background color
        logout_icon_label = Label(collapsed_icon_frame, image=logout_icon, bg=icon_bg_color)
        logout_icon_label.pack(side='bottom', padx=10, pady=10)
        logout_icon_label.bind("<Button-1>", lambda event: logout())

        collapsed_icon_frame.pack(side='left', fill='y')

    def toggle_theme():
        current_bg = MenuFrame.cget('bg')
        if current_bg == "#f8f8f8":
            # Dark theme
            MenuFrame.configure(bg="#2c2c2c")
            top_canvas.configure(bg="#2c2c2c")
            content_frame.configure(bg="#2c2c2c")
            category_frame.configure(bg="#696969")
            collapsed_icon_frame.configure(bg="#696969")

            # Update category button colors
            for btn in category_buttons:
                btn.configure(bg="#858585", fg='white')

            # Update logout button colors
            logout_btn.configure(bg="#858585", fg='white')

            # Update category icon labels for dark theme
            for category_icon_label in collapsed_icon_frame.winfo_children():
                if isinstance(category_icon_label, Label):
                    category_icon_label.configure(bg="#696969")

            # Update logout icon label for dark theme
            for widget in collapsed_icon_frame.winfo_children():
                if isinstance(widget, Label) and widget.cget('image') == str(logout_icon):
                    widget.configure(bg="#696969")

            # Update icons for dark mode
            toggle_theme_btn.configure(image=dark_mode_icon)

        else:
            # Light theme
            MenuFrame.configure(bg="#f8f8f8")
            top_canvas.configure(bg="black")
            content_frame.configure(bg="#f8f8f8")
            category_frame.configure(bg="#C3C3C3")
            collapsed_icon_frame.configure(bg="#C3C3C3")

            # Update category button colors
            for btn in category_buttons:
                btn.configure(bg="#919191", fg='black')

            # Update logout button colors
            logout_btn.configure(bg='#919191', fg='black')

            # Update category icon labels for light theme
            for category_icon_label in collapsed_icon_frame.winfo_children():
                if isinstance(category_icon_label, Label):
                    category_icon_label.configure(bg="#C3C3C3")

            # Update logout icon label for light theme
            for widget in collapsed_icon_frame.winfo_children():
                if isinstance(widget, Label) and widget.cget('image') == str(logout_icon):
                    widget.configure(bg="#C3C3C3")

            # Update icons for light mode
            toggle_theme_btn.configure(image=light_mode_icon)

    root.withdraw()
    form_frame.withdraw()

    MenuFrame = Toplevel()
    MenuFrame.title("Tenant Dashboard")
    MenuFrame.geometry("1920x1080+0+0")
    MenuFrame.state("zoomed")
    MenuFrame.configure(bg="#f8f8f8")

    # Load the GIF frames
    gif_image_path = "image\\water.gif"  # Replace with the actual gif path
    gif_image = Image.open(gif_image_path)

    # Resize the GIF to desired dimensions (e.g., 1920x150)
    desired_width, desired_height = 1920, 150
    gif_frames = []

    try:
        while True:
            resized_frame = gif_image.resize((desired_width, desired_height), Image.Resampling.LANCZOS)
            gif_frame = ImageTk.PhotoImage(resized_frame)
            gif_frames.append(gif_frame)
            gif_image.seek(len(gif_frames))  # Go to the next frame
    except EOFError:
        pass

    gif_frames_count = len(gif_frames)

    # Create the canvas to hold the GIF and other elements
    top_canvas = Canvas(MenuFrame, width=1920, height=150, bg="black", highlightbackground="black",
                        highlightcolor="black", highlightthickness=2)
    top_canvas.pack(fill='x')

    # Add the GIF to the canvas
    gif_image_id = top_canvas.create_image(0, 0, image=gif_frames[0], anchor='nw')

    # Function to animate the GIF
    def animate_gif(frame_index):
        top_canvas.itemconfig(gif_image_id, image=gif_frames[frame_index])
        frame_index = (frame_index + 1) % gif_frames_count
        top_canvas.after(100, animate_gif, frame_index)

    # Start the GIF animation
    animate_gif(0)

    # Load icons for toggle buttons
    open_icon = ImageTk.PhotoImage(Image.open("image\\open_menu.png").resize((30, 30), Image.Resampling.LANCZOS))
    close_icon = ImageTk.PhotoImage(Image.open("image\\close_menu.png").resize((30, 30), Image.Resampling.LANCZOS))
    light_mode_icon = ImageTk.PhotoImage(
        Image.open("image\\bright_mode.png").resize((35, 35), Image.Resampling.LANCZOS))
    dark_mode_icon = ImageTk.PhotoImage(Image.open("image\\dark_mode.png").resize((35, 35), Image.Resampling.LANCZOS))

    # Load category icons
    stall_icon = ImageTk.PhotoImage(Image.open("image\\stall.png").resize((30, 30), Image.Resampling.LANCZOS))
    apply_stall_icon = ImageTk.PhotoImage(
        Image.open("image\\apply_stall.png").resize((30, 30), Image.Resampling.LANCZOS))
    payment_icon = ImageTk.PhotoImage(Image.open("image\\payment.png").resize((30, 30), Image.Resampling.LANCZOS))
    notification_icon = ImageTk.PhotoImage(
        Image.open("image\\notification.png").resize((30, 30), Image.Resampling.LANCZOS))
    feedback_icon = ImageTk.PhotoImage(Image.open("image\\feedback.png").resize((30, 30), Image.Resampling.LANCZOS))
    profiles_icon = ImageTk.PhotoImage(Image.open("image\\profiles.png").resize((30, 30), Image.Resampling.LANCZOS))

    # List of icons corresponding to each category
    category_icons = {
        "Stall": stall_icon,
        "Apply Stall": apply_stall_icon,
        "Payment": payment_icon,
        "Notification": notification_icon,
        "Feedback": feedback_icon,
        "Profiles": profiles_icon
    }

    # Create a frame for collapsed icons
    collapsed_icon_frame = Frame(MenuFrame, bg="#C3C3C3", height=500, width=50)  # Adjust the width as needed

    # Create title text on the canvas
    title_text_id = top_canvas.create_text(800, 40, text="Tenant Dashboard", font=('Algerian', 45, 'bold'),
                                           fill='white')

    # Create text for selected category
    selected_category = StringVar(value="Stall")
    selected_category_text_id = top_canvas.create_text(760, 100, text=selected_category.get(),
                                                       font=('Bauhaus 93', 18, 'bold', 'underline'), fill='#796796')
    top_canvas.itemconfigure(selected_category_text_id, state='hidden')
    # Load and crop the user's profile picture
    profile_image = Image.open("image\\people.png")  # Replace with the actual image path
    profile_image = profile_image.resize((50, 50), Image.Resampling.LANCZOS)

    # Create a mask for the circular crop
    mask = Image.new("L", profile_image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((1, 1, 49, 49), fill=255)

    # Apply the mask to the profile image
    profile_image.putalpha(mask)

    # Convert to PhotoImage
    profile_image_tk = ImageTk.PhotoImage(profile_image)

    # Add profile picture on the canvas
    profile_image_id = top_canvas.create_image(20, 100, image=profile_image_tk, anchor='nw')
    top_canvas.profile_image_tk = profile_image_tk

    # Add username text beside profile picture
    username_text_id = top_canvas.create_text(90, 135, text=logged_in_user['username'],
                                              font=('Arial', 16, 'underline', 'bold'), fill='blue', anchor='w')
    top_canvas.tag_bind(username_text_id, "<Button-1>", open_edit_user_info_and_close_dashboard)

    # Add date and time text on the canvas
    date_time_text_id = top_canvas.create_text(1400, 130, font=('Arial', 12, 'bold'), fill='white')

    # Function to update the date and time text
    def update_time_and_date():
        now = datetime.datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        day_str = now.strftime("%A")
        formatted_str = f"{date_str}    {time_str}    {day_str}"
        top_canvas.itemconfig(date_time_text_id, text=formatted_str)
        top_canvas.after(1000, update_time_and_date)

    # Start updating the time and date
    update_time_and_date()

    # Button to toggle theme, placed beside the date and time
    toggle_theme_btn = Button(MenuFrame, image=light_mode_icon, command=toggle_theme, bg='black', borderwidth=0)
    top_canvas.toggle_theme_btn_id = top_canvas.create_window(1230, 110, anchor='nw', window=toggle_theme_btn)

    # Create frame for category buttons
    category_frame = Frame(MenuFrame, bg="#C3C3C3", height=500, width=200)  # Adjust size as needed
    category_frame.pack(side='left', fill='y')  # Initially visible

    toggle_category_btn = Button(category_frame, image=close_icon, command=toggle_categories, bg='black', borderwidth=0)
    toggle_category_btn.pack(side='top', anchor='w', pady=10, padx=10)  # Anchor it to the top-left with padding

    # Define tenant dashboard categories
    categories = ["Stall", "Apply Stall", "Payment", "Notification", "Feedback", "Profiles"]
    category_buttons = []

    # Pack buttons vertically in the category frame
    for category in categories:
        btn = Button(category_frame, text=category, image=category_icons[category], compound='left',
                     command=lambda c=category: update_selected_category(c),
                     height=35, anchor='w', font=('Arial', 14, 'bold'), fg='black', bg='#919191', borderwidth=0, padx=5)
        btn.pack(side='top', fill='x', padx=10, pady=10)
        category_buttons.append(btn)

    # Load the logout icon
    logout_icon = ImageTk.PhotoImage(Image.open("image\\logout.png").resize((30, 30), Image.Resampling.LANCZOS))

    logout_btn = Button(category_frame, text="Logout", compound='left', image=logout_icon, command=logout,
                        height=35, anchor='w', font=('Arial', 14, 'bold'), fg='black', bg='#919191', borderwidth=0,
                        padx=5)
    logout_btn.pack(side='bottom', fill='x', padx=10, pady=10)

    # Frame for displaying dynamic content
    content_frame = Frame(MenuFrame, bg="#f8f8f8")
    content_frame.pack(side='top', fill='both', expand=True, padx=20, pady=(10, 10))  # Place above bottom frame

    # Trigger the default category (Stall) to load on startup
    update_selected_category("Stall")

def fetch_tenant_id(username, password):
    conn = sqlite3.connect("stall_rental_system.db")
    cursor = conn.cursor()

    try:
        query = """
                SELECT tenant_id
                FROM tenant
                WHERE username = ? AND password = ?
                """
        cursor.execute(query, (username, password))
        tenant_data = cursor.fetchone()

        if not tenant_data:
            raise sqlite3.Error("Tenant not found")

        tenant_id = tenant_data[0]  # Extract tenant_id from the fetched data
        return tenant_id

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return None

def get_tenant_rental_info(tenant_id, period):
    # Connect to the database
    conn = sqlite3.connect('stall_rental_system.db')
    cursor = conn.cursor()

    # Query to fetch the tenant's full name, IC, and phone number from the tenant table
    cursor.execute("""
        SELECT fullname, ic, phone_number FROM tenant WHERE tenant_id = ?
    """, (tenant_id,))
    tenant = cursor.fetchone()

    # Query to fetch the stall ID, rental period, rent price, and rental_id from the payments table
    cursor.execute("""
        SELECT s.stall_id, p.paid_periods, p.amount, p.rental_id 
        FROM payment p
        JOIN rental r ON p.rental_id = r.rental_id
        JOIN stall s ON r.stall_id = s.stall_id
        WHERE p.tenant_id = ? AND p.paid_periods = ?
    """, (tenant_id, period))
    payment = cursor.fetchone()

    # Close the database connection
    conn.close()

    # Return the tenant and payment details
    if tenant and payment:
        fullname, ic, phone_number = tenant
        stall_id, paid_periods, rent_price, rental_id = payment
        return fullname, ic, phone_number, stall_id, rent_price, rental_id
    else:
        return None

def generate_receipt(tenant_id, period):
    # Get the tenant and payment information from the database
    tenant_info = get_tenant_rental_info(tenant_id, period)  # Update this function to filter by period

    if tenant_info:
        fullname, ic, phone_number, stall_id, rent_price, rental_id = tenant_info  # Remove period here

        pdf = FPDF()

        # Add a page
        pdf.add_page()

        # Set the business information in the header
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, "GOVERNMENT STALL RENTAL SYSTEM", ln=True, align='C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(200, 10, "TEL NO: 6011-2828477", ln=True, align='C')
        pdf.cell(200, 10, "HELPLINE: 1800-200-255", ln=True, align='C')
        pdf.cell(200, 10, "EMAIL: projectall2.2024@gmail.com", ln=True, align='C')

        # Add tenant details (formatted like in the image)
        pdf.set_font("Arial", '', 12)

        # First row: Tenant Name and Phone Number
        pdf.cell(100, 10, f"Tenant Name: {fullname}", ln=False)
        pdf.cell(90, 10, f"Phone Number: {phone_number}", ln=True, align='R')

        # Second row: IC and Date
        pdf.cell(100, 10, f"IC: {ic}", ln=False)
        pdf.cell(90, 10, f"Date: {datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S')}", ln=True, align='R')

        # Add space
        pdf.ln(20)

        # Add line above the Stall ID section
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())

        # Header for Stall details (mimicking table-like layout without borders)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(60, 10, "Stall ID", border=0, align='C')
        pdf.cell(70, 10, "Period (Months)", border=0, align='C')
        pdf.cell(60, 10, "Amount (RM)", border=0, align='C', ln=True)

        # Add line below the header
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())

        # Values for Stall ID, Period, and Amount, aligned in the center
        pdf.set_font("Arial", '', 12)
        pdf.cell(60, 10, f"{stall_id}", border=0, align='C')
        pdf.cell(70, 10, f"{period}", border=0, align='C')  # Use the period passed
        pdf.cell(60, 10, f"RM {rent_price}", border=0, align='C', ln=True)

        # Add line after values
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())

        # Add rental ID (aligned to the left)
        pdf.ln(10)
        pdf.cell(200, 10, f"Rental ID: {rental_id}", ln=True, align='C')

        # Add a "Thank you for your payment" message
        pdf.ln(10)
        pdf.cell(200, 10, "Thank you for your payment!", ln=True, align='C')

        # Generate the PDF filename with tenant's name and period
        pdf_output_name = f"Receipt_{fullname}_Period_{period}.pdf"
        pdf.output(pdf_output_name)

        # Open the generated PDF automatically
        webbrowser.open(pdf_output_name)

        print(f"Receipt for {fullname} generated successfully as {pdf_output_name}.")
    else:
        print("Tenant or payment information not found.")

def send_email_with_receipt(tenant_email, admin_email, pdf_filename, fullname):
    # Create the email for the tenant
    tenant_msg = MIMEMultipart()
    tenant_msg['From'] = admin_email
    tenant_msg['To'] = tenant_email
    tenant_msg['Subject'] = f"Payment Receipt for {fullname}"

    # Email body for tenant
    tenant_body = f"Dear {fullname},\n\nThank you for your payment. Please find attached your payment receipt.\n\n\nBest regards,\nGovernment Stall Rental System"
    tenant_msg.attach(MIMEText(tenant_body, 'plain'))

    # Attach the PDF receipt
    with open(pdf_filename, 'rb') as attachment:
        part = MIMEApplication(attachment.read(), _subtype='pdf')
        part.add_header('Content-Disposition', f'attachment; filename={pdf_filename}')
        tenant_msg.attach(part)

    # Create the email for the admin
    admin_msg = MIMEMultipart()
    admin_msg['From'] = admin_email
    admin_msg['To'] = admin_email  # Sending to the same admin email
    admin_msg['Subject'] = f"Receipt Generated for {fullname}"

    # Email body for admin
    admin_body = f"Dear Admin,\n\nA payment receipt has been generated for {fullname}. Please find the attached PDF."
    admin_msg.attach(MIMEText(admin_body, 'plain'))

    # Attach the same PDF receipt for admin
    with open(pdf_filename, 'rb') as attachment:
        part = MIMEApplication(attachment.read(), _subtype='pdf')
        part.add_header('Content-Disposition', f'attachment; filename={pdf_filename}')
        admin_msg.attach(part)

    # Send emails to tenant and admin
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(admin_email, 'xiim atxo oajc mtly')  # Use the appropriate email password
            # Send the email to the tenant
            server.send_message(tenant_msg)
            # Send the email to the admin
            server.send_message(admin_msg)
            print(f"Receipt emailed to {tenant_email} and notification sent to admin at {admin_email}.")
    except Exception as e:
        print(f"Failed to send email: {e}")

def insert_notification_for_all_admins(message):
    # Get all admin IDs
    cursor.execute("SELECT admin_id FROM admin")
    admin_ids = cursor.fetchall()

    for admin_id in admin_ids:
        # Insert notification for each admin
        insert_notification("admin", admin_id[0], message)

def insert_notification(recipient_type, recipient_id, message):
    # Get the current time
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Insert notification into the database
    cursor.execute("""
        INSERT INTO notification (recipient, recipient_id, message, notification_date)
        VALUES (?, ?, ?, ?)
    """, (recipient_type, recipient_id, message, current_time))
    conn.commit()


#send notification for tenant who no take attendance today
def has_attendance_taken_today(tenant_id):
    # Function to check if attendance has been taken today
    # if already send the notification and email no need to send again
    today = datetime.date.today()
    cursor.execute("""
        SELECT COUNT(*) FROM attendance_records
        WHERE tenant_id = ? AND DATE(attendance_time) = ?
    """, (tenant_id, today))
    return cursor.fetchone()[0] > 0

def send_email_attendance(recipient_email, subject, message):
    # Function to send email
    try:
        # Set up your email server details here
        sender_email = "projectall2.2024@gmail.com"
        sender_password = "xiim atxo oajc mtly"  # Use environment variables or secure storage for passwords

        msg = MIMEText(message)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient_email

        # Use Gmail's SMTP server
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        print("Email sent successfully!")
    except Exception as e:
        print(f"Failed to send email: {e}")

def has_notification_been_sent(tenant_id, message):
    # Function to check if a notification with the same message has already been sent today
    today = datetime.date.today()
    cursor.execute("""
        SELECT COUNT(*) FROM notification
        WHERE recipient_id = ? AND message = ? AND DATE(notification_date) = ?
    """, (tenant_id, message, today))
    return cursor.fetchone()[0] > 0

def check_all_attendance_and_notify():
    # Function to check and send notification if no attendance has been taken by noon for all tenants
    today = datetime.date.today()
    now = datetime.datetime.now()

    # Only check if the current time is after noon
    if now.hour >= 12:
        # Retrieve tenant IDs and email addresses for tenants who currently have rentals
        cursor.execute("""
            SELECT tenant.tenant_id, tenant.email_address 
            FROM tenant
            JOIN rental ON tenant.tenant_id = rental.tenant_id
        """)
        tenants = cursor.fetchall()

        # Prepare the attendance reminder message
        subject = "Attendance Reminder"
        message = "Dear Tenant,\n\nYou have not taken attendance today. Please remember to do so.\n\n\nBest regards,\nGovernment Stall Rental System"

        for tenant_id, email_address in tenants:
            if not has_attendance_taken_today(tenant_id):
                # Check if the notification has already been sent today
                if not has_notification_been_sent(tenant_id, message):
                    # Send email
                    send_email_attendance(email_address, subject, message)

                    # Get the current time
                    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                    # Insert notification into the notification table
                    cursor.execute("""
                        INSERT INTO notification (recipient, recipient_id, message, notification_date)
                        VALUES (?, ?, ?, ?)
                    """, ("tenant", tenant_id, message, current_time))

                    # Commit the changes to the database
                    conn.commit()

                    print(f"Notification sent to tenant ID {tenant_id}. Email sent to {email_address}.")
                else:
                    print(f"Notification already sent to tenant ID {tenant_id} today. No need to send again.")




# Login & Register
# Global variable to store the after callback ID
# Define global variables
animation_callback_id = None
animation_running = False

def animate_text():
    global animation_callback_id, animation_running
    text = "GOVERNMENT STALL RENTAL SYSTEM"
    delay = 100  # Delay in milliseconds between each letter
    canvas.delete("text")  # Clear previous text

    # Cancel any ongoing animation to prevent overlay issues
    if animation_callback_id is not None:
        form_frame.after_cancel(animation_callback_id)

    animation_running = True  # Set animation state

    def animate_step(i):
        global animation_callback_id
        if i <= len(text):
            canvas.delete("text")
            canvas.create_text(
                canvas.winfo_width() / 2, 30,
                text=text[:i],
                font=('Bernard MT Condensed', 38, 'bold'),
                fill="white",
                tags="text"
            )
            form_frame.update()  # Refresh the form_frame to show the new character
            animation_callback_id = form_frame.after(delay, animate_step, i + 1)
        else:
            animation_running = False  # Reset animation state
            animation_callback_id = form_frame.after(1000, animate_text)  # Restart animation after a pause

    animate_step(0)  # Start the animation

def update_text_position(event):
    canvas_width = canvas.winfo_width()
    center_x = canvas_width / 2
    top_y = 30

    # Update the text position without animation
    canvas.coords("text", center_x, top_y)

def LoginForm():
    global LoginFrame, lbl_result1, form_frame, openEye_button, openEye_status
    global password, openEyeButton_image, closeEyeButton_image, canvas

    root.withdraw()

    form_frame = Toplevel()
    form_frame.title("Register and Login")
    form_frame.geometry("1920x1080+0+0")
    form_frame.state("zoomed")

    # Load the background image
    image = Image.open("image\\background.png").convert("RGBA")
    resized_image = image.resize((1550, 800), Image.Resampling.LANCZOS)

    # Adjust transparency
    alpha = 190  # Transparency level (0 is fully transparent, 255 is fully opaque)
    alpha_channel = resized_image.split()[3].point(lambda p: p * alpha / 255.)
    transparent_image = Image.merge("RGBA", (resized_image.split()[:3] + (alpha_channel,)))

    # Convert the image to a format tkinter can handle
    bg_image = ImageTk.PhotoImage(transparent_image)

    # Create canvas and add background
    canvas = Canvas(form_frame, width=1920, height=1080)
    canvas.place(x=0, y=0, relwidth=1, relheight=1)
    canvas.create_image(0, 0, anchor='nw', image=bg_image)

    # Bind resize to adjust text position only
    form_frame.bind("<Configure>", update_text_position)

    # Create and place LoginFrame directly, without delay
    global LoginFrame
    LoginFrame = Frame(form_frame, highlightbackground="black", highlightcolor="black", highlightthickness=2,
                       bg="white")
    LoginFrame.place(relx=0.5, rely=0.5, anchor='center')

    # Add content to LoginFrame immediately
    lbl_title = Label(LoginFrame, text="Login:", font=('Script MT Bold', 24, 'bold'), fg='#0016BA', bg="white")
    lbl_title.grid(row=0, columnspan=5, pady=5)

    # Start the text animation in the background
    form_frame.after(0, animate_text)

    # Keep a reference to images
    form_frame.image = bg_image

    lbl_username = Label(LoginFrame, text="Username:", font=('times new roman', 16), bd=18, bg="white")
    lbl_username.grid(row=1, column=0, padx=5)

    lbl_password = Label(LoginFrame, text="Password:", font=('times new roman', 16), bd=18, bg="white")
    lbl_password.grid(row=2, column=0, padx=5)

    # Load and place the icons
    people_icon = ImageTk.PhotoImage(Image.open("image\\people.png").resize((20, 20)))
    lock_icon = ImageTk.PhotoImage(Image.open("image\\lock.png").resize((20, 20)))

    lbl_people_icon = Label(LoginFrame, image=people_icon, bg="white")
    lbl_people_icon.grid(row=1, column=1, padx=(0, 1))  # Adjust the padding as needed

    lbl_lock_icon = Label(LoginFrame, image=lock_icon, bg="white")
    lbl_lock_icon.grid(row=2, column=1, padx=(0, 1))  # Adjust the padding as needed

    # Clear existing text in the entry fields
    USERNAME_LOGIN.set("")
    PASSWORD_LOGIN.set("")

    username = Entry(LoginFrame, font=('times new roman', 14), textvariable=USERNAME_LOGIN, width=20,
                     highlightbackground="black", highlightcolor="black", highlightthickness=1)
    username.grid(row=1, column=2, padx=10)
    username.insert(0, "Username")  # Placeholder for username
    username.config(fg='grey')  # Set placeholder text color to grey
    username.bind("<FocusIn>", lambda event: on_entry_click(username, "Username"))
    username.bind("<FocusOut>", lambda event: on_focus_out(username, "Username"))

    password = Entry(LoginFrame, font=('times new roman', 14), textvariable=PASSWORD_LOGIN, width=20,
                     highlightbackground="black", highlightcolor="black", highlightthickness=1)
    password.grid(row=2, column=2, padx=10)
    password.insert(0, "Password")  # Placeholder for password
    password.config(fg='grey', show='')  # Set placeholder text color to grey and disable password masking
    password.bind("<FocusIn>", lambda event: password_on_focus_in(password, "Password"))
    password.bind("<FocusOut>", lambda event: password_on_focus_out(password, "Password"))
    password.bind("<KeyRelease>",
                  lambda event: check_password_field())  # Bind to check the password field on key release

    # Load eye icons for show/hide password
    openEyeButton_image = ImageTk.PhotoImage(Image.open("image\\open_eye.png").resize((20, 20)))
    closeEyeButton_image = ImageTk.PhotoImage(Image.open("image\\closed_eye.png").resize((20, 20)))

    openEye_button = Button(LoginFrame, image=closeEyeButton_image, command=show_password)
    openEye_button.grid(row=2, column=3, padx=5)
    openEye_button.config(state='disabled')  # Initially disable the eye button

    openEye_status = Label(LoginFrame, text='Close', bg="white")  # Track the status of the eye button
    openEye_status.grid(row=2, column=4)
    openEye_status.grid_remove()

    # Add "Forgot Password?" link at the bottom right of the password field
    forgot_password = Label(LoginFrame, text="Forgot Password?", fg="#00A4FF", font=('arial', 10), bg="white")
    forgot_password.bind('<Enter>', lambda event, label=forgot_password: label.config(font=('arial', 10, 'underline')))
    forgot_password.bind('<Leave>', lambda event, label=forgot_password: label.config(font=('arial', 10)))
    forgot_password.bind('<Button-1>', lambda event: forgot_password_action())  # Replace with your actual function
    forgot_password.grid(row=3, column=2, sticky='e')

    btn_login = ctk.CTkButton(LoginFrame, text="Login", font=('times new roman', 22, 'bold'), command=Login,
                              fg_color='#A5AAF7', text_color='white', corner_radius=50)
    btn_login.bind("<Enter>", lambda e: btn_login.configure(fg_color="#B9BFFF"))
    btn_login.bind("<Leave>", lambda e: btn_login.configure(fg_color="#A5AAF7"))
    btn_login.grid(row=4, columnspan=5, pady=5)

    # Add "or" label between Login and Face Recognition buttons
    lbl_or = Label(LoginFrame, text="or", font=('times new roman', 14), bg="white")
    lbl_or.grid(row=5, columnspan=5)

    # Face Recognition button
    btn_face_recognition = ctk.CTkButton(LoginFrame, text="Face Login", font=('times new roman', 22, 'bold'),
                                         command=face_recognition_login, fg_color='#A5AAF7', text_color='white',
                                         corner_radius=50)
    btn_face_recognition.bind("<Enter>", lambda e: btn_face_recognition.configure(fg_color="#B9BFFF"))
    btn_face_recognition.bind("<Leave>", lambda e: btn_face_recognition.configure(fg_color="#A5AAF7"))
    btn_face_recognition.grid(row=6, columnspan=5, pady=5)

    lbl_text = Label(LoginFrame, text="Not registered?", font=('times new roman', 14), bg="white")
    lbl_text.grid(row=7, columnspan=5)

    # Create a frame to hold both register labels
    register_frame = Frame(LoginFrame, bg="white")
    register_frame.grid(row=8, columnspan=5, pady=5)  # Place in the grid, centered horizontally

    # "Tenant Register" label
    lbl_register = Label(register_frame, text="Tenant Register", fg="#00A4FF", font=('arial', 11), bg="white")
    lbl_register.bind('<Enter>', lambda event, label=lbl_register: label.config(font=('arial', 11, 'underline')))
    lbl_register.bind('<Leave>', lambda event, label=lbl_register: label.config(font=('arial', 11)))
    lbl_register.bind('<Button-1>', ToggleToRegister)
    lbl_register.grid(row=0, column=0, padx=(0, 5))  # Add padding between Tenant and Admin Register

    # "or" label
    lbl_text = Label(register_frame, text="or", font=('times new roman', 11), bg="white")
    lbl_text.grid(row=0, column=1, padx=(5, 5))  # Center the "or" text

    # "Admin Register" label
    lbl_adminregister = Label(register_frame, text="Admin Register", fg="red", font=('arial', 11), bg="white")
    lbl_adminregister.bind('<Enter>',
                           lambda event, label=lbl_adminregister: label.config(font=('arial', 11, 'underline')))
    lbl_adminregister.bind('<Leave>', lambda event, label=lbl_adminregister: label.config(font=('arial', 11)))
    lbl_adminregister.bind('<Button-1>', ToggleToAdminRegister)
    lbl_adminregister.grid(row=0, column=2, padx=(5, 0))  # Add padding between "or" and Admin Register

    lbl_text = Label(register_frame, text="or", font=('times new roman', 11), bg="white")
    lbl_text.grid(row=0, column=3, padx=(5, 5))  # Center the "or" text

    # "Auditor Register" label
    lbl_auditorregister = Label(register_frame, text="Auditor Register", fg="green", font=('arial', 11), bg="white")
    lbl_auditorregister.bind('<Enter>',
                             lambda event, label=lbl_auditorregister: label.config(font=('arial', 11, 'underline')))
    lbl_auditorregister.bind('<Leave>', lambda event, label=lbl_auditorregister: label.config(font=('arial', 11)))
    lbl_auditorregister.bind('<Button-1>', ToggleToAuditorRegister)
    lbl_auditorregister.grid(row=0, column=4, padx=(5, 0))  # Add padding between "or" and Admin Register

    def position_about_us_text(event=None):
        # Center "About Us" text and icon on the canvas
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()

        # Position the icon and text near the bottom center
        canvas.coords(about_us_icon, canvas_width / 2 - 40, canvas_height - 30)  # Icon position
        canvas.coords(about_us_text, canvas_width / 2 + 10, canvas_height - 30)  # Text position

    # Load the icon image
    icon_image = Image.open("image\\about.png").resize((20, 20), Image.Resampling.LANCZOS)  # Adjust path and size
    about_us_icon_image = ImageTk.PhotoImage(icon_image)

    # Create icon and text on canvas
    about_us_icon = canvas.create_image(960, 1030, image=about_us_icon_image, anchor='center')
    about_us_text = canvas.create_text(1000, 1030, text="About Us", fill="black", font=('arial', 12, 'bold'))

    # Bind hover and click events for the text
    canvas.tag_bind(about_us_text, '<Enter>',
                    lambda event: canvas.itemconfig(about_us_text, font=('arial', 12, 'bold', 'underline')))
    canvas.tag_bind(about_us_text, '<Leave>',
                    lambda event: canvas.itemconfig(about_us_text, font=('arial', 12, 'bold')))
    canvas.tag_bind(about_us_text, '<Button-1>', lambda event: show_about_info())
    canvas.tag_bind(about_us_icon, '<Button-1>', lambda event: show_about_info())  # Clickable icon

    # Bind resize event to keep icon and text centered
    form_frame.bind("<Configure>", position_about_us_text)

    # Prevent garbage collection of the icon image
    canvas.about_us_icon_image = about_us_icon_image

    # Keep a reference to the image object to prevent garbage collection
    form_frame.image = bg_image
    form_frame.people_icon = people_icon
    form_frame.lock_icon = lock_icon

def show_about_info():
    about_info = (
        "Welcome to the Government Stall Rental System!\n\n"
        "For any inquiries, please contact:\n"
        "Email: projectall2.2024@gmail.com\n"
        "Phone: +601163230109\n\n"
        "Thank you for using our system!"
    )

    messagebox.showinfo("About", about_info)

def face_recognition_login():
    """
    Capture a face via the webcam, verify it using the stored face embeddings,
    and redirect to the appropriate dashboard based on the user's role.
    """
    global logged_in_user  # Declare the global variable to modify it

    try:
        # Open the webcam
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open webcam.")
            return

        # Display a message box prompting the user to capture their face
        messagebox.showinfo("Info", "Please press 's' to capture your face")

        # Start capturing frames
        while True:
            ret, frame = cap.read()
            if not ret:
                messagebox.showerror("Error", "Failed to capture face image.")
                break

            # Show the captured frame
            cv2.imshow("Webcam", frame)

            # Capture the image if 's' is pressed
            if cv2.waitKey(1) & 0xFF == ord('s'):
                break  # Exit the loop to process the captured image

        cap.release()  # Release the webcam
        cv2.destroyAllWindows()  # Close the webcam window

        # Convert the captured frame to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect face location and encoding in the captured frame
        face_locations = face_recognition.face_locations(frame_rgb)
        if not face_locations:
            messagebox.showerror("Error", "No face detected. Please try again.")
            return

        face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)
        if not face_encodings:
            messagebox.showerror("Error", "Failed to encode face. Please try again.")
            return

        # Compare the captured face encoding with stored face embeddings
        captured_encoding = face_encodings[0]
        username = verify_face_embedding(captured_encoding)  # Verify the captured face with stored embeddings

        if username:
            # Fetch the password from the database based on the username for tenant, admin, and auditor roles
            cursor.execute("SELECT password FROM tenant WHERE username = ?", (username,))
            tenant_password = cursor.fetchone()

            cursor.execute("SELECT password FROM admin WHERE username = ?", (username,))
            admin_password = cursor.fetchone()

            cursor.execute("SELECT password FROM auditor WHERE username = ?", (username,))
            auditor_password = cursor.fetchone()

            # Store the logged-in user's info in the global variable
            logged_in_user['username'] = username
            logged_in_user['password'] = (
                tenant_password[0] if tenant_password else
                admin_password[0] if admin_password else
                auditor_password[0] if auditor_password else None
            )
            logged_in_user['role'] = (
                'tenant' if tenant_password else
                'admin' if admin_password else
                'auditor' if auditor_password else None
            )

            # Redirect to the appropriate dashboard
            if tenant_password:
                messagebox.showinfo("Success", f"Welcome, {username}! Redirecting to tenant dashboard...")
                tenant_dashboard()  # Replace with your tenant dashboard function
            elif admin_password:
                messagebox.showinfo("Success", f"Welcome, {username}! Redirecting to admin dashboard...")
                admin_dashboard()  # Replace with your admin dashboard function
            elif auditor_password:
                messagebox.showinfo("Success", f"Welcome, {username}! Redirecting to auditor dashboard...")
                auditor_dashboard()  # Replace with your auditor dashboard function
        else:
            messagebox.showerror("Error", "Face not recognized. Please try again or register your Face ID.")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred during face recognition: {e}")
        print(f"Error details: {e}")

def verify_face_embedding(captured_encoding):
    """
    Compare the captured face encoding with stored face embeddings in the database
    and return the username of the closest match if it meets strict distance requirements.
    """
    try:
        # Fetch all usernames and face embeddings from the tenant and admin tables
        cursor.execute("SELECT username, face_embedding FROM tenant")
        tenants = cursor.fetchall()

        cursor.execute("SELECT username, face_embedding FROM admin")
        admins = cursor.fetchall()

        # Combine tenants and admins for a global search
        all_users = tenants + admins

        # Set a stricter threshold for face comparison (smaller values = stricter match)
        face_distance_threshold = 0.4  # can change
        best_match_username = None
        smallest_distance = float("inf")  # Initialize with infinity for comparison

        # Loop through all users and compare their face embedding with the captured encoding
        for user in all_users:
            username = user[0]
            stored_embedding_bytes = user[1]

            if stored_embedding_bytes:
                stored_embedding = np.frombuffer(stored_embedding_bytes, dtype=np.float64)  # Convert back to array

                # Compute face distance between captured encoding and stored embedding
                face_distance = np.linalg.norm(captured_encoding - stored_embedding)

                # Update condition: if the distance is smaller and below a stricter threshold
                if face_distance < face_distance_threshold and face_distance < smallest_distance:
                    smallest_distance = face_distance
                    best_match_username = username

        # Check if the smallest distance is sufficiently small to avoid false positives
        if best_match_username and smallest_distance < face_distance_threshold:
            print(f"Best match found with username: {best_match_username} (Distance: {smallest_distance})")
            return best_match_username
        else:
            # No match found or too distant match
            print(f"No close match found (Distance: {smallest_distance})")
            return None

    except Exception as e:
        print(f"Error occurred while verifying face embedding: {e}")
        return None

def generate_verification_code():
    # Function to generate a random verification code
    return str(random.randint(100000, 999999))

def send_verification_code(email, verification_code):
    try:
        sender_email = "projectall2.2024@gmail.com"  # Replace with your email
        sender_password = "xiim atxo oajc mtly"  # Replace with your email password

        # Create the email content
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Password Reset Verification Code"

        body = f"Dear User,\n\nYour verification code is: {verification_code}\n\n\nBest regards,\nGovernment Stall Rental System"
        msg.attach(MIMEText(body, 'plain'))

        # Set up the server
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Replace with your email provider's SMTP server
        server.starttls()
        server.login(sender_email, sender_password)

        # Send the email
        server.sendmail(sender_email, email, msg.as_string())
        server.quit()
        messagebox.showinfo("Success", "Verification code sent to your email")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to send verification code. Error: {str(e)}")

def forgot_password_action():
    verification_code = generate_verification_code()

    def add_placeholder(entry, placeholder):
        entry.config(show='')  # Temporarily remove masking
        entry.insert(0, placeholder)
        entry.config(fg='grey')

    def remove_placeholder(event, entry, placeholder):
        if entry.get() == placeholder:
            entry.delete(0, END)
            entry.config(fg='black')
            if entry == new_password_entry or entry == confirm_password_entry:
                entry.config(show='*')  # Reapply masking for password fields

    def restore_placeholder(event, entry, placeholder):
        if entry.get() == '':
            add_placeholder(entry, placeholder)
            entry.config(show='')  # Ensure no masking for the placeholder

    def toggle_password_visibility(entry_widget, button, status, placeholder):
        if entry_widget.get() == '' or entry_widget.get() == placeholder:
            return  # Do nothing if the entry is empty or only contains the placeholder
        if entry_widget.cget('show') == '*':
            entry_widget.config(show='')
            button.config(image=show_eye_image)
            status.set('Show')
        else:
            entry_widget.config(show='*')
            button.config(image=hide_eye_image)
            status.set('Hide')

    forgot_password_window = Toplevel()
    forgot_password_window.title("Forgot Password")
    forgot_password_window.geometry("620x400")
    forgot_password_window.configure(bg="white")

    center_frame = ctk.CTkFrame(forgot_password_window, fg_color='#E0E0E0', corner_radius=50)
    center_frame.pack(pady=20, padx=20, anchor='center')

    form_frame = ctk.CTkFrame(center_frame, fg_color='#E0E0E0', corner_radius=50)
    form_frame.pack(pady=20, padx=20, fill='both', expand=True)

    Label(form_frame, text="Reset Password:", font=('Bernard MT Condensed', 18, 'bold'), bg='#E0E0E0').grid(row=0,
                                                                                                            column=0,
                                                                                                            columnspan=3,
                                                                                                            pady=10)

    Label(form_frame, text="Username:", font=('Arial', 12), bg='#E0E0E0').grid(row=1, column=0, sticky='w', padx=10,
                                                                               pady=5)
    username_entry = Entry(form_frame, font=('Arial', 12), width=30, highlightbackground="black",
                           highlightcolor="black", highlightthickness=1)
    username_entry.grid(row=1, column=1, padx=10, pady=5)
    add_placeholder(username_entry, "Enter your username")
    username_entry.bind("<FocusIn>", lambda event: remove_placeholder(event, username_entry, "Enter your username"))
    username_entry.bind("<FocusOut>", lambda event: restore_placeholder(event, username_entry, "Enter your username"))

    Label(form_frame, text="Email:", font=('Arial', 12), bg='#E0E0E0').grid(row=2, column=0, sticky='w', padx=10,
                                                                            pady=5)
    email_entry = Entry(form_frame, font=('Arial', 12), width=30, highlightbackground="black", highlightcolor="black",
                        highlightthickness=1)
    email_entry.grid(row=2, column=1, padx=10, pady=5)
    add_placeholder(email_entry, "Enter your email")
    email_entry.bind("<FocusIn>", lambda event: remove_placeholder(event, email_entry, "Enter your email"))
    email_entry.bind("<FocusOut>", lambda event: restore_placeholder(event, email_entry, "Enter your email"))

    Label(form_frame, text="Verification Code:", font=('Arial', 12), bg='#E0E0E0').grid(row=3, column=0, sticky='w',
                                                                                        padx=10, pady=5)
    verification_entry = Entry(form_frame, font=('Arial', 12), width=30, highlightbackground="black",
                               highlightcolor="black", highlightthickness=1)
    verification_entry.grid(row=3, column=1, padx=10, pady=5)
    add_placeholder(verification_entry, "Enter verification code")
    verification_entry.bind("<FocusIn>",
                            lambda event: remove_placeholder(event, verification_entry, "Enter verification code"))
    verification_entry.bind("<FocusOut>",
                            lambda event: restore_placeholder(event, verification_entry, "Enter verification code"))

    # Button to send verification code
    send_code_button = ctk.CTkButton(form_frame, text="get code",
                                     command=lambda: send_verification_code_if_exists(email_entry.get().strip(),
                                                                                      username_entry.get().strip(),
                                                                                      verification_code),
                                     font=("Arial", 10, "bold"), fg_color='#00527B', text_color='white',
                                     corner_radius=50, width=15)
    send_code_button.grid(row=3, column=2, padx=5, pady=5)

    Label(form_frame, text="New Password:", font=('Arial', 12), bg='#E0E0E0').grid(row=4, column=0, sticky='w', padx=10,
                                                                                   pady=5)
    new_password_entry = Entry(form_frame, font=('Arial', 12), width=30, show='*', highlightbackground="black",
                               highlightcolor="black", highlightthickness=1)
    new_password_entry.grid(row=4, column=1, padx=10, pady=5)
    add_placeholder(new_password_entry, "Enter new password")
    new_password_entry.config(show='')  # Initially show the placeholder text without masking
    new_password_entry.bind("<FocusIn>",
                            lambda event: remove_placeholder(event, new_password_entry, "Enter new password"))
    new_password_entry.bind("<FocusOut>",
                            lambda event: restore_placeholder(event, new_password_entry, "Enter new password"))

    Label(form_frame, text="Confirm Password:", font=('Arial', 12), bg='#E0E0E0').grid(row=5, column=0, sticky='w',
                                                                                       padx=10, pady=5)
    confirm_password_entry = Entry(form_frame, font=('Arial', 12), width=30, show='*', highlightbackground="black",
                                   highlightcolor="black", highlightthickness=1)
    confirm_password_entry.grid(row=5, column=1, padx=10, pady=5)
    add_placeholder(confirm_password_entry, "Confirm new password")
    confirm_password_entry.config(show='')  # Initially show the placeholder text without masking
    confirm_password_entry.bind("<FocusIn>",
                                lambda event: remove_placeholder(event, confirm_password_entry, "Confirm new password"))
    confirm_password_entry.bind("<FocusOut>", lambda event: restore_placeholder(event, confirm_password_entry,
                                                                                "Confirm new password"))

    # Load images for eye buttons
    show_eye_image = ImageTk.PhotoImage(Image.open("image\\open_eye.png").resize((15, 15)))
    hide_eye_image = ImageTk.PhotoImage(Image.open("image\\closed_eye.png").resize((15, 15)))

    # New Password Eye Button
    new_password_status = StringVar(value='Hide')
    new_password_eye_button = Button(form_frame, image=hide_eye_image,
                                     command=lambda: toggle_password_visibility(new_password_entry,
                                                                                new_password_eye_button,
                                                                                new_password_status,
                                                                                "Enter new password"))
    new_password_eye_button.grid(row=4, column=2, padx=5, pady=5, sticky='e')

    # Confirm Password Eye Button
    confirm_password_status = StringVar(value='Hide')
    confirm_password_eye_button = Button(form_frame, image=hide_eye_image,
                                         command=lambda: toggle_password_visibility(confirm_password_entry,
                                                                                    confirm_password_eye_button,
                                                                                    confirm_password_status,
                                                                                    "Confirm new password"))
    confirm_password_eye_button.grid(row=5, column=2, padx=5, pady=5, sticky='e')

    # Change Password Button
    change_password_button = ctk.CTkButton(form_frame, text="Change Password", font=('Arial', 18, 'bold'),
                                           fg_color='#00527B', text_color='white', corner_radius=50,
                                           command=lambda: change_password(forgot_password_window, email_entry,
                                                                           username_entry, new_password_entry,
                                                                           confirm_password_entry, verification_entry,
                                                                           verification_code))
    change_password_button.bind("<Enter>", lambda e: change_password_button.configure(fg_color='#0075B0'))
    change_password_button.bind("<Leave>", lambda e: change_password_button.configure(fg_color='#00527B'))
    change_password_button.grid(row=6, column=0, columnspan=3, pady=20)

def send_verification_code_if_exists(email, username, verification_code):
    # Connect to the database
    conn = sqlite3.connect('stall_rental_system.db')
    cursor = conn.cursor()

    # Check if user exists in the tenant table
    cursor.execute("SELECT * FROM tenant WHERE email_address = ? AND username = ?", (email, username))
    tenant = cursor.fetchone()

    if tenant:
        # If tenant exists, send verification code
        send_verification_code(email, verification_code)
    else:
        # Check if user exists in the admin table
        cursor.execute("SELECT * FROM admin WHERE email_address = ? AND username = ?", (email, username))
        admin = cursor.fetchone()

        if admin:
            # If admin exists, send verification code
            send_verification_code(email, verification_code)
        else:
            # Check if user exists in the auditor table
            cursor.execute("SELECT * FROM auditor WHERE email_address = ? AND username = ?", (email, username))
            auditor = cursor.fetchone()

            if auditor:
                # If auditor exists, send verification code
                send_verification_code(email, verification_code)
            else:
                # User not found in all tables
                messagebox.showerror("Error", "User not found")

    conn.close()

def change_password(window, email_entry, username_entry, new_password_entry, confirm_password_entry, verification_entry,
                    verification_code):
    # Get the values from the entry widgets
    email = email_entry.get().strip()
    username = username_entry.get().strip()
    new_password = new_password_entry.get().strip()
    confirm_password = confirm_password_entry.get().strip()
    input_code = verification_entry.get().strip()

    # Validate inputs
    if not email or not username or not new_password or not confirm_password:
        messagebox.showerror("Error", "All fields must be filled out")
        return

    if not verify_email_code(input_code, verification_code):
        return

    if new_password != confirm_password:
        messagebox.showerror("Error", "Passwords do not match")
        return

    # Connect to the database
    conn = sqlite3.connect('stall_rental_system.db')
    cursor = conn.cursor()

    # Check if user exists in the tenant table
    cursor.execute("SELECT * FROM tenant WHERE email_address = ? AND username = ?", (email, username))
    tenant = cursor.fetchone()

    if tenant:
        # Update the user's password in the tenant table
        cursor.execute("UPDATE tenant SET password = ? WHERE email_address = ? AND username = ?",
                       (new_password, email, username))
        conn.commit()
        messagebox.showinfo("Success", "Password updated successfully")
        window.destroy()  # Close the forgot password window
    else:
        # Check if user exists in the admin table
        cursor.execute("SELECT * FROM admin WHERE email_address = ? AND username = ?", (email, username))
        admin = cursor.fetchone()

        if admin:
            # Update the admin's password in the admin table
            cursor.execute("UPDATE admin SET password = ? WHERE email_address = ? AND username = ?",
                           (new_password, email, username))
            conn.commit()
            messagebox.showinfo("Success", "Password updated successfully")
            window.destroy()  # Close the forgot password window
        else:
            # Check if user exists in the auditor table
            cursor.execute("SELECT * FROM auditor WHERE email_address = ? AND username = ?", (email, username))
            auditor = cursor.fetchone()

            if auditor:
                # Update the auditor's password in the auditor table
                cursor.execute("UPDATE auditor SET password = ? WHERE email_address = ? AND username = ?",
                               (new_password, email, username))
                conn.commit()
                messagebox.showinfo("Success", "Password updated successfully")
                window.destroy()  # Close the forgot password window
            else:
                messagebox.showerror("Error", "User not found")

    conn.close()

def verify_email_code(input_code, actual_code):
    if input_code.strip() != actual_code.strip():
        messagebox.showerror("Error", "Invalid verification code")
        return False
    return True

def password_on_focus_in(entry, placeholder):
    if entry.get() == placeholder:
        entry.delete(0, "end")  # Clear the placeholder text
        entry.config(fg='black', show='*')  # Set text color to black and enable password masking

def password_on_focus_out(entry, placeholder):
    if entry.get() == "":
        entry.insert(0, placeholder)  # Restore placeholder text if the field is empty
        entry.config(fg='grey', show='')  # Set placeholder text color to grey and disable password masking

def check_password_field():
    # Enable or disable the eye button based on the password field content
    if password.get() == "" or password.get() == "Password":
        openEye_button.config(state='disabled')
    else:
        openEye_button.config(state='normal')

def show_password():
    # Toggle the password visibility
    if openEye_status.cget('text') == 'Close':
        openEye_button.configure(image=openEyeButton_image)
        password.config(show='')  # Show the password
        openEye_status.configure(text='Open')
    elif openEye_status.cget('text') == 'Open':
        openEye_button.configure(image=closeEyeButton_image)
        password.config(show='*')  # Hide the password
        openEye_status.configure(text='Close')

def on_entry_click(entry, placeholder):
    """function that gets called whenever entry is clicked"""
    if entry.get() == placeholder:
        entry.delete(0, "end")  # delete all the text in the entry
        entry.insert(0, '')  # Insert blank for user input
        entry.config(fg='black')

def on_focus_out(entry, placeholder):
    """function that gets called whenever entry is clicked out"""
    if entry.get() == '':
        entry.insert(0, placeholder)
        entry.config(fg='grey')

def setup_combobox_styles():
    style = ttk.Style()
    style.configure('TCombobox', foreground='black', background='white', font=('times new roman', 20))

def RegisterForm(ic_number=None):
    global RegisterFrame, lbl_result2, confirm_password_entry, password, openEye_button, confirm_openEye_button
    global openEye_status, confirm_openEye_status, openEyeButton_image, closeEyeButton_image
    global USERNAME_REGISTER, PASSWORD_REGISTER, FULLNAME, IC, EMAIL_ADDRESS, PHONE_NUMBER, DATE_OF_BIRTH, day_var, month_var, year_var
    global entered_code

    root.withdraw()

    RegisterFrame = Frame(form_frame, highlightbackground="black", highlightcolor="black", highlightthickness=2)
    RegisterFrame.pack(side='top', pady=(60, 20))

    lbl_login = Label(RegisterFrame, text="Click to Login", fg="#00A4FF", font=('arial', 12))
    lbl_login.bind('<Enter>', lambda event, label=lbl_login: label.config(font=('arial', 12, 'underline')))
    lbl_login.bind('<Leave>', lambda event, label=lbl_login: label.config(font=('arial', 12)))
    lbl_login.grid(row=12, columnspan=4, pady=5)
    lbl_login.bind('<Button-1>', ToggleToLogin)

    lbl_result2 = Label(RegisterFrame, text="Registration Form:", font=('Script MT Bold', 24, 'bold'), fg='#0016BA',
                        bd=18)
    lbl_result2.grid(row=1, columnspan=4)

    lbl_username = Label(RegisterFrame, text="Username:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_username.grid(row=2)

    lbl_password = Label(RegisterFrame, text="Password:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_password.grid(row=3)

    lbl_confirm_password = Label(RegisterFrame, text="Confirm Password:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_confirm_password.grid(row=4)

    lbl_fullname = Label(RegisterFrame, text="Full Name:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_fullname.grid(row=5)

    lbl_ic = Label(RegisterFrame, text="IC:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_ic.grid(row=6)

    lbl_date_of_birth = Label(RegisterFrame, text="Date of Birth:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_date_of_birth.grid(row=7)

    lbl_email_address = Label(RegisterFrame, text="Email Address:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_email_address.grid(row=8)

    lbl_phone_number = Label(RegisterFrame, text="Phone number:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_phone_number.grid(row=9)

    # Clear existing text in the entry fields
    USERNAME_REGISTER.set("")
    PASSWORD_REGISTER.set("")
    FULLNAME.set("")
    EMAIL_ADDRESS.set("")
    PHONE_NUMBER.set("")
    DATE_OF_BIRTH = StringVar()
    entered_code = StringVar()

    username = Entry(RegisterFrame, font=('times new roman', 15), textvariable=USERNAME_REGISTER, width=20,
                     highlightbackground="black", highlightcolor="black", highlightthickness=1)
    username.grid(row=2, column=1, padx=10)
    username.insert(0, "Enter your username")
    username.config(fg='grey')
    username.bind("<FocusIn>", lambda event: on_entry_click(username, "Enter your username"))
    username.bind("<FocusOut>", lambda event: on_focus_out(username, "Enter your username"))

    password = Entry(RegisterFrame, font=('times new roman', 15), textvariable=PASSWORD_REGISTER, width=20,
                     highlightbackground="black", highlightcolor="black", highlightthickness=1)
    password.grid(row=3, column=1, padx=10)
    password.insert(0, "Enter your password")
    password.config(fg='grey')
    password.bind("<FocusIn>", lambda event: password_on_focus_in(password, "Enter your password"))
    password.bind("<FocusOut>", lambda event: password_on_focus_out(password, "Enter your password"))
    password.bind("<KeyRelease>", lambda event: check_password_field_register())

    confirm_password_entry = Entry(RegisterFrame, font=('times new roman', 15), width=20, highlightbackground="black",
                                   highlightcolor="black", highlightthickness=1)
    confirm_password_entry.grid(row=4, column=1, padx=10)
    confirm_password_entry.insert(0, "Confirm your password")
    confirm_password_entry.config(fg='grey')
    confirm_password_entry.bind("<FocusIn>",
                                lambda event: password_on_focus_in(confirm_password_entry, "Confirm your password"))
    confirm_password_entry.bind("<FocusOut>",
                                lambda event: password_on_focus_out(confirm_password_entry, "Confirm your password"))
    confirm_password_entry.bind("<KeyRelease>", lambda event: check_confirm_password_field_register())

    fullname = Entry(RegisterFrame, font=('times new roman', 15), textvariable=FULLNAME, width=20,
                     highlightbackground="black", highlightcolor="black", highlightthickness=1)
    fullname.grid(row=5, column=1, padx=10)
    fullname.insert(0, "Enter your full name")
    fullname.config(fg='grey')
    fullname.bind("<FocusIn>", lambda event: on_entry_click(fullname, "Enter your full name"))
    fullname.bind("<FocusOut>", lambda event: on_focus_out(fullname, "Enter your full name"))

    # Configure IC entry field to be pre-filled and readonly
    IC.set(ic_number)  # Set the provided IC number
    ic = Entry(RegisterFrame, font=('times new roman', 15), textvariable=IC, width=20, highlightbackground="black",
               highlightcolor="black", highlightthickness=1, state="readonly")
    ic.grid(row=6, column=1, padx=10)

    # Create Date of Birth dropdowns
    setup_combobox_styles()

    day_var = StringVar(RegisterFrame)
    month_var = StringVar(RegisterFrame)
    year_var = StringVar(RegisterFrame)

    days = [str(i).zfill(2) for i in range(1, 32)]
    months = [str(i).zfill(2) for i in range(1, 13)]

    # Get the current year dynamically and create a list of years from the current year going backward
    current_year = datetime.datetime.now().year
    years = [str(i) for i in range(current_year, 1899, -1)]  # Start from the current year and go back to 1900

    day_menu = ttk.Combobox(RegisterFrame, textvariable=day_var, values=days, width=8, state="readonly",
                            style='TCombobox')
    day_menu.grid(row=7, column=1, sticky="w", padx=10)
    day_menu.set("day")

    month_menu = ttk.Combobox(RegisterFrame, textvariable=month_var, values=months, width=8, state="readonly",
                              style='TCombobox')
    month_menu.grid(row=7, column=1)
    month_menu.set("month")

    year_menu = ttk.Combobox(RegisterFrame, textvariable=year_var, values=years, width=8, state="readonly",
                             style='TCombobox')
    year_menu.grid(row=7, column=1, sticky="e", padx=10)
    year_menu.set("year")

    # Store the selected date of birth in the DATE_OF_BIRTH variable
    def update_dob():
        if day_var.get() != "day" and month_var.get() != "month" and year_var.get() != "year":
            DATE_OF_BIRTH.set(f"{day_var.get()}-{month_var.get()}-{year_var.get()}")
        else:
            DATE_OF_BIRTH.set("")

    day_var.trace("w", lambda *args: update_dob())
    month_var.trace("w", lambda *args: update_dob())
    year_var.trace("w", lambda *args: update_dob())

    email_address = Entry(RegisterFrame, font=('times new roman', 15), textvariable=EMAIL_ADDRESS, width=20,
                          highlightbackground="black", highlightcolor="black", highlightthickness=1)
    email_address.grid(row=8, column=1, padx=10)
    email_address.insert(0, "Enter your email address")
    email_address.config(fg='grey')
    email_address.bind("<FocusIn>", lambda event: on_entry_click(email_address, "Enter your email address"))
    email_address.bind("<FocusOut>", lambda event: on_focus_out(email_address, "Enter your email address"))

    phone_number = Entry(RegisterFrame, font=('times new roman', 15), textvariable=PHONE_NUMBER, width=20,
                         highlightbackground="black", highlightcolor="black", highlightthickness=1)
    phone_number.grid(row=9, column=1, padx=10)
    phone_number.insert(0, "Enter your phone number")
    phone_number.config(fg='grey')
    phone_number.bind("<FocusIn>", lambda event: on_entry_click(phone_number, "Enter your phone number"))
    phone_number.bind("<FocusOut>", lambda event: on_focus_out(phone_number, "Enter your phone number"))

    openEyeButton_image = ImageTk.PhotoImage(Image.open("image\\open_eye.png").resize((20, 20)))
    closeEyeButton_image = ImageTk.PhotoImage(Image.open("image\\closed_eye.png").resize((20, 20)))

    openEye_button = Button(RegisterFrame, image=closeEyeButton_image, command=show_password_register)
    openEye_button.grid(row=3, column=2, padx=5)
    openEye_button.config(state='disabled')

    openEye_status = Label(RegisterFrame, text='Close')
    openEye_status.grid(row=3, column=3)
    openEye_status.grid_remove()

    confirm_openEye_button = Button(RegisterFrame, image=closeEyeButton_image, command=show_confirm_password_register)
    confirm_openEye_button.grid(row=4, column=2, padx=5)
    confirm_openEye_button.config(state='disabled')

    confirm_openEye_status = Label(RegisterFrame, text='Close')
    confirm_openEye_status.grid(row=4, column=3)
    confirm_openEye_status.grid_remove()

    # Add a button to send the verification code to the user's email
    btn_send_code = ctk.CTkButton(RegisterFrame, text="get code", font=('times new roman', 15, 'bold'), width=15,
                                  command=lambda: send_verification_email(EMAIL_ADDRESS), corner_radius=50)
    btn_send_code.grid(row=10, column=2, padx=5)

    # Add a field for the user to enter the verification code
    lbl_verification_code = Label(RegisterFrame, text="Verification Code:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_verification_code.grid(row=10, column=0)

    verification_code_entry = Entry(RegisterFrame, textvariable=entered_code, font=('times new roman', 15), width=20,
                                    highlightbackground="black", highlightcolor="black", highlightthickness=1)
    verification_code_entry.insert(0, "Enter verification code")
    verification_code_entry.config(fg='grey')
    verification_code_entry.bind("<FocusIn>",
                                 lambda event: on_entry_click(verification_code_entry, "Enter verification code"))
    verification_code_entry.bind("<FocusOut>",
                                 lambda event: on_focus_out(verification_code_entry, "Enter verification code"))
    verification_code_entry.grid(row=10, column=1, padx=10)

    # Add a button to verify the entered code
    btn_verify_code = ctk.CTkButton(RegisterFrame, text="Register", font=('times new roman', 22, 'bold'),
                                    fg_color='#A5AAF7',
                                    text_color='white', corner_radius=50, command=verify_code_input)
    btn_verify_code.bind("<Enter>", lambda e: btn_verify_code.configure(fg_color="#B9BFFF"))
    btn_verify_code.bind("<Leave>", lambda e: btn_verify_code.configure(fg_color="#A5AAF7"))
    btn_verify_code.grid(row=11, columnspan=3, pady=10)

def is_valid_date(day, month, year):
    from datetime import datetime

    try:
        datetime(int(year), int(month), int(day))
        return True
    except ValueError:
        return False

def check_password_field_register():
    if password.get() == "" or password.get() == "Enter your password":
        openEye_button.config(state='disabled')
    else:
        openEye_button.config(state='normal')

def check_confirm_password_field_register():
    if confirm_password_entry.get() == "" or confirm_password_entry.get() == "Confirm your password":
        confirm_openEye_button.config(state='disabled')
    else:
        confirm_openEye_button.config(state='normal')

def show_password_register():
    if openEye_status.cget('text') == 'Close':
        openEye_button.configure(image=openEyeButton_image)
        password.config(show='')  # Show the password
        openEye_status.configure(text='Open')
    elif openEye_status.cget('text') == 'Open':
        openEye_button.configure(image=closeEyeButton_image)
        password.config(show='*')  # Hide the password
        openEye_status.configure(text='Close')

def show_confirm_password_register():
    if confirm_openEye_status.cget('text') == 'Close':
        confirm_openEye_button.configure(image=openEyeButton_image)
        confirm_password_entry.config(show='')  # Show the password
        confirm_openEye_status.configure(text='Open')
    elif confirm_openEye_status.cget('text') == 'Open':
        confirm_openEye_button.configure(image=closeEyeButton_image)
        confirm_password_entry.config(show='*')  # Hide the password
        confirm_openEye_status.configure(text='Close')

def AdminRegisterForm():
    global AdminRegisterFrame, lbl_result2, confirm_password_entry, password, openEye_button, confirm_openEye_button
    global openEye_status, confirm_openEye_status, openEyeButton_image, closeEyeButton_image
    global USERNAME_REGISTER, PASSWORD_REGISTER, FULLNAME, IC, EMAIL_ADDRESS, PHONE_NUMBER, DATE_OF_BIRTH, day_var, month_var, year_var
    global entered_code

    root.withdraw()

    AdminRegisterFrame = Frame(form_frame, highlightbackground="black", highlightcolor="black", highlightthickness=2)
    AdminRegisterFrame.pack(side='top', pady=(60, 20))

    lbl_login = Label(AdminRegisterFrame, text="Click to Login", fg="#00A4FF", font=('arial', 12))
    lbl_login.bind('<Enter>', lambda event, label=lbl_login: label.config(font=('arial', 12, 'underline')))
    lbl_login.bind('<Leave>', lambda event, label=lbl_login: label.config(font=('arial', 12)))
    lbl_login.grid(row=12, columnspan=4, pady=5)
    lbl_login.bind('<Button-1>', AdminToggleToLogin)

    lbl_result2 = Label(AdminRegisterFrame, text="Admin Registration Form:", font=('Script MT Bold', 24, 'bold'),
                        fg='#0016BA',
                        bd=18)
    lbl_result2.grid(row=1, columnspan=4)

    lbl_username = Label(AdminRegisterFrame, text="Username:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_username.grid(row=2)

    lbl_password = Label(AdminRegisterFrame, text="Password:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_password.grid(row=3)

    lbl_confirm_password = Label(AdminRegisterFrame, text="Confirm Password:", font=('times new roman', 15, 'bold'),
                                 bd=18)
    lbl_confirm_password.grid(row=4)

    lbl_fullname = Label(AdminRegisterFrame, text="Full Name:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_fullname.grid(row=5)

    lbl_ic = Label(AdminRegisterFrame, text="IC:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_ic.grid(row=6)

    lbl_date_of_birth = Label(AdminRegisterFrame, text="Date of Birth:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_date_of_birth.grid(row=7)

    lbl_email_address = Label(AdminRegisterFrame, text="Email Address:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_email_address.grid(row=8)

    lbl_phone_number = Label(AdminRegisterFrame, text="Phone number:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_phone_number.grid(row=9)

    # Clear existing text in the entry fields
    USERNAME_REGISTER.set("")
    PASSWORD_REGISTER.set("")
    FULLNAME.set("")
    IC.set("")
    EMAIL_ADDRESS.set("")
    PHONE_NUMBER.set("")
    DATE_OF_BIRTH = StringVar()
    entered_code = StringVar()

    username = Entry(AdminRegisterFrame, font=('times new roman', 15), textvariable=USERNAME_REGISTER, width=20,
                     highlightbackground="black", highlightcolor="black", highlightthickness=1)
    username.grid(row=2, column=1, padx=10)
    username.insert(0, "Enter your username")
    username.config(fg='grey')
    username.bind("<FocusIn>", lambda event: on_entry_click(username, "Enter your username"))
    username.bind("<FocusOut>", lambda event: on_focus_out(username, "Enter your username"))

    password = Entry(AdminRegisterFrame, font=('times new roman', 15), textvariable=PASSWORD_REGISTER, width=20,
                     highlightbackground="black", highlightcolor="black", highlightthickness=1)
    password.grid(row=3, column=1, padx=10)
    password.insert(0, "Enter your password")
    password.config(fg='grey')
    password.bind("<FocusIn>", lambda event: password_on_focus_in(password, "Enter your password"))
    password.bind("<FocusOut>", lambda event: password_on_focus_out(password, "Enter your password"))
    password.bind("<KeyRelease>", lambda event: check_password_field_register())

    confirm_password_entry = Entry(AdminRegisterFrame, font=('times new roman', 15), width=20,
                                   highlightbackground="black",
                                   highlightcolor="black", highlightthickness=1)
    confirm_password_entry.grid(row=4, column=1, padx=10)
    confirm_password_entry.insert(0, "Confirm your password")
    confirm_password_entry.config(fg='grey')
    confirm_password_entry.bind("<FocusIn>",
                                lambda event: password_on_focus_in(confirm_password_entry, "Confirm your password"))
    confirm_password_entry.bind("<FocusOut>",
                                lambda event: password_on_focus_out(confirm_password_entry, "Confirm your password"))
    confirm_password_entry.bind("<KeyRelease>", lambda event: check_confirm_password_field_register())

    fullname = Entry(AdminRegisterFrame, font=('times new roman', 15), textvariable=FULLNAME, width=20,
                     highlightbackground="black", highlightcolor="black", highlightthickness=1)
    fullname.grid(row=5, column=1, padx=10)
    fullname.insert(0, "Enter your full name")
    fullname.config(fg='grey')
    fullname.bind("<FocusIn>", lambda event: on_entry_click(fullname, "Enter your full name"))
    fullname.bind("<FocusOut>", lambda event: on_focus_out(fullname, "Enter your full name"))

    ic = Entry(AdminRegisterFrame, font=('times new roman', 15), textvariable=IC, width=20, highlightbackground="black",
               highlightcolor="black", highlightthickness=1)
    ic.grid(row=6, column=1, padx=10)
    ic.insert(0, "Enter your IC")
    ic.config(fg='grey')
    ic.bind("<FocusIn>", lambda event: on_entry_click(ic, "Enter your IC"))
    ic.bind("<FocusOut>", lambda event: on_focus_out(ic, "Enter your IC"))

    # Create Date of Birth dropdowns
    setup_combobox_styles()

    day_var = StringVar(AdminRegisterFrame)
    month_var = StringVar(AdminRegisterFrame)
    year_var = StringVar(AdminRegisterFrame)

    days = [str(i).zfill(2) for i in range(1, 32)]
    months = [str(i).zfill(2) for i in range(1, 13)]
    # Get the current year
    current_year = datetime.datetime.now().year
    # Create a list of years starting from the current year going backward to 1900
    years = [str(i) for i in range(current_year, 1899, -1)]

    day_menu = ttk.Combobox(AdminRegisterFrame, textvariable=day_var, values=days, width=8, state="readonly",
                            style='TCombobox')
    day_menu.grid(row=7, column=1, sticky="w", padx=10)
    day_menu.set("day")

    month_menu = ttk.Combobox(AdminRegisterFrame, textvariable=month_var, values=months, width=8, state="readonly",
                              style='TCombobox')
    month_menu.grid(row=7, column=1)
    month_menu.set("month")

    year_menu = ttk.Combobox(AdminRegisterFrame, textvariable=year_var, values=years, width=8, state="readonly",
                             style='TCombobox')
    year_menu.grid(row=7, column=1, sticky="e", padx=10)
    year_menu.set("year")

    # Store the selected date of birth in the DATE_OF_BIRTH variable
    def update_dob():
        if day_var.get() != "day" and month_var.get() != "month" and year_var.get() != "year":
            DATE_OF_BIRTH.set(f"{day_var.get()}-{month_var.get()}-{year_var.get()}")
        else:
            DATE_OF_BIRTH.set("")

    day_var.trace("w", lambda *args: update_dob())
    month_var.trace("w", lambda *args: update_dob())
    year_var.trace("w", lambda *args: update_dob())

    email_address = Entry(AdminRegisterFrame, font=('times new roman', 15), textvariable=EMAIL_ADDRESS, width=20,
                          highlightbackground="black", highlightcolor="black", highlightthickness=1)
    email_address.grid(row=8, column=1, padx=10)
    email_address.insert(0, "Enter your email address")
    email_address.config(fg='grey')
    email_address.bind("<FocusIn>", lambda event: on_entry_click(email_address, "Enter your email address"))
    email_address.bind("<FocusOut>", lambda event: on_focus_out(email_address, "Enter your email address"))

    phone_number = Entry(AdminRegisterFrame, font=('times new roman', 15), textvariable=PHONE_NUMBER, width=20,
                         highlightbackground="black", highlightcolor="black", highlightthickness=1)
    phone_number.grid(row=9, column=1, padx=10)
    phone_number.insert(0, "Enter your phone number")
    phone_number.config(fg='grey')
    phone_number.bind("<FocusIn>", lambda event: on_entry_click(phone_number, "Enter your phone number"))
    phone_number.bind("<FocusOut>", lambda event: on_focus_out(phone_number, "Enter your phone number"))

    openEyeButton_image = ImageTk.PhotoImage(Image.open("image\\open_eye.png").resize((20, 20)))
    closeEyeButton_image = ImageTk.PhotoImage(Image.open("image\\closed_eye.png").resize((20, 20)))

    openEye_button = Button(AdminRegisterFrame, image=closeEyeButton_image, command=show_password_register)
    openEye_button.grid(row=3, column=2, padx=5)
    openEye_button.config(state='disabled')

    openEye_status = Label(AdminRegisterFrame, text='Close')
    openEye_status.grid(row=3, column=3)
    openEye_status.grid_remove()

    confirm_openEye_button = Button(AdminRegisterFrame, image=closeEyeButton_image,
                                    command=show_confirm_password_register)
    confirm_openEye_button.grid(row=4, column=2, padx=5)
    confirm_openEye_button.config(state='disabled')

    confirm_openEye_status = Label(AdminRegisterFrame, text='Close')
    confirm_openEye_status.grid(row=4, column=3)
    confirm_openEye_status.grid_remove()

    # Add a button to send the verification code to the user's email
    btn_send_code = ctk.CTkButton(AdminRegisterFrame, text="get code", font=('times new roman', 15, 'bold'), width=15,
                                  command=lambda: send_verification_email(EMAIL_ADDRESS), corner_radius=50)
    btn_send_code.grid(row=10, column=2, padx=5)

    # Add a field for the user to enter the verification code
    lbl_verification_code = Label(AdminRegisterFrame, text="Verification Code:", font=('times new roman', 15, 'bold'),
                                  bd=18)
    lbl_verification_code.grid(row=10, column=0)

    verification_code_entry = Entry(AdminRegisterFrame, textvariable=entered_code, font=('times new roman', 15),
                                    width=20,
                                    highlightbackground="black", highlightcolor="black", highlightthickness=1)
    verification_code_entry.insert(0, "Enter verification code")
    verification_code_entry.config(fg='grey')
    verification_code_entry.bind("<FocusIn>",
                                 lambda event: on_entry_click(verification_code_entry, "Enter verification code"))
    verification_code_entry.bind("<FocusOut>",
                                 lambda event: on_focus_out(verification_code_entry, "Enter verification code"))
    verification_code_entry.grid(row=10, column=1, padx=10)

    # Add a button to verify the entered code
    btn_verify_code = ctk.CTkButton(AdminRegisterFrame, text="Register", font=('times new roman', 22, 'bold'),
                                    fg_color='#A5AAF7',
                                    text_color='white', corner_radius=50, command=verify_code_input_admin)
    btn_verify_code.bind("<Enter>", lambda e: btn_verify_code.configure(fg_color="#B9BFFF"))
    btn_verify_code.bind("<Leave>", lambda e: btn_verify_code.configure(fg_color="#A5AAF7"))
    btn_verify_code.grid(row=11, columnspan=3, pady=10)

def AdminRegister():
    Database()
    admin = Admin(conn, cursor)
    tenant = Tenant(conn, cursor)
    auditor = Auditor(conn, cursor)

    try:
        placeholders = {
            "USERNAME_REGISTER": "Enter your admin username",
            "PASSWORD_REGISTER": "Enter your admin password",
            "FULLNAME": "Enter your full name",
            "IC": "Enter your IC (optional)",
            "DATE_OF_BIRTH": "Enter day-month-year",
            "EMAIL_ADDRESS": "Enter your email address",
            "PHONE_NUMBER": "Enter your phone number"
        }

        # Check if any field is empty or contains placeholder text (adjust IC to optional)
        if (USERNAME_REGISTER.get() in ("", placeholders["USERNAME_REGISTER"]) or
                PASSWORD_REGISTER.get() in ("", placeholders["PASSWORD_REGISTER"]) or
                FULLNAME.get() in ("", placeholders["FULLNAME"]) or
                confirm_password_entry.get() in ("", placeholders["PASSWORD_REGISTER"]) or
                DATE_OF_BIRTH.get() in ("", placeholders["DATE_OF_BIRTH"]) or
                EMAIL_ADDRESS.get() in ("", placeholders["EMAIL_ADDRESS"]) or
                PHONE_NUMBER.get() in ("", placeholders["PHONE_NUMBER"])):
            messagebox.showerror("Error", "Please complete all the required fields!")
            return

        # Check if the IC is provided and if it has the correct format
        ic = IC.get()
        if ic:  # If IC is provided (optional field)
            ic_pattern = r"^\d{6}-\d{2}-\d{4}$"
            if not re.match(ic_pattern, ic):
                messagebox.showerror("Error", "IC must be in the format XXXXXX-XX-XXXX (6 digits-2 digits-4 digits)!")
                return

            # Ensure IC is unique across both admin and tenant tables
            if admin.get_admin_by_ic(ic) or tenant.get_tenant_by_ic(ic) or auditor.get_auditor_by_ic(ic):
                messagebox.showerror("Error", "IC number is already registered!")
                return

        # Check if the date of birth is valid
        day, month, year = DATE_OF_BIRTH.get().split('-')
        if not is_valid_date(day, month, year):
            messagebox.showerror("Error", "Invalid date of birth!")
            return

        # Validate username length
        username = USERNAME_REGISTER.get()
        if not (6 <= len(username) <= 20):
            messagebox.showerror("Error", "Username must be between 6 and 20 characters!")
            return

        # Validate password length
        password = PASSWORD_REGISTER.get()
        if not (6 <= len(password) <= 20):
            messagebox.showerror("Error", "Password must be between 6 and 20 characters!")
            return

        # Check if passwords match
        if password != confirm_password_entry.get():
            messagebox.showerror("Error", "Password and Confirm Password do not match!")
            return

        # Validate email format (must end with @gmail.com)
        email = EMAIL_ADDRESS.get()
        if not email.endswith("@gmail.com"):
            messagebox.showerror("Error", "Email must be a valid Gmail address ending with @gmail.com!")
            return

        # Validate phone number
        phone_number = PHONE_NUMBER.get()
        if not (phone_number.startswith("60") and phone_number.isdigit() and 11 <= len(phone_number) <= 12):
            messagebox.showerror("Error", "Phone number must start with '60' and be 11 to 12 digits long!")
            return

        # Ensure username is unique across both admin and tenant tables
        if admin.get_admin_by_username(username) or tenant.get_tenant_by_username(
                username) or auditor.get_auditor_by_username(username):
            messagebox.showerror("Error", "Username is already taken!")
            return

        # Register the new admin
        admin.register_admin(username, password, FULLNAME.get(), IC.get(), DATE_OF_BIRTH.get(), email, phone_number)

        # Clear input fields after successful registration
        USERNAME_REGISTER.set("")
        PASSWORD_REGISTER.set("")
        FULLNAME.set("")
        IC.set("")
        DATE_OF_BIRTH.set("")
        EMAIL_ADDRESS.set("")
        PHONE_NUMBER.set("")
        confirm_password_entry.delete(0, 'end')

        # Reset day, month, and year comboboxes (if applicable)
        day_var.set("day")
        month_var.set("month")
        year_var.set("year")

        messagebox.showinfo("Success", "Admin registered successfully. Now, please register your Face ID.")

        # Open Face ID registration window, passing the stored username
        register_face_id(username)

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error occurred during registration: {e}")

def ToggleToLogin(event=None):
    if RegisterFrame is not None:
        form_frame.withdraw()
        RegisterFrame.destroy()
    # Clear any previous text and animation before switching forms
    canvas.delete("text")  # Clear any text on the canvas
    animate_text()  # Start the text animation
    LoginForm()

def AdminToggleToLogin(event=None):
    if AdminRegisterFrame is not None:
        form_frame.withdraw()
        AdminRegisterFrame.destroy()
    # Clear any previous text and animation before switching forms
    canvas.delete("text")  # Clear any text on the canvas
    animate_text()  # Start the text animation
    LoginForm()

def ToggleToRegister(event=None):
    def check_ic_and_proceed():
        ic = ic_entry.get().strip()

        if ic:
            try:
                # Query to check if the IC exists in the tenant table
                cursor.execute("SELECT * FROM tenant WHERE ic = ?", (ic,))
                existing_tenant = cursor.fetchone()

                if existing_tenant:
                    tenant_id, username, password, fullname, ic, date_of_birth, email_address, phone_number, face_id_image, face_embedding = existing_tenant

                    if any(field is None for field in
                           [username, password, fullname, date_of_birth, email_address, phone_number]):
                        messagebox.showinfo("Registration Required", "Please complete your registration.")
                        ic_popup.destroy()
                        RegisterForm(ic_number=ic)  # Pass the IC number to the registration form
                    else:
                        messagebox.showinfo("Account Exists", "You already have an account.")
                        ic_popup.destroy()
                else:
                    messagebox.showerror("Error", "IC number not found. Please check your entry.")
                    ic_popup.destroy()

            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Database error: {e}")
                ic_popup.destroy()
        else:
            messagebox.showwarning("Warning", "Please enter your IC number.")

    # Create a popup to enter IC number
    ic_popup = Toplevel()
    ic_popup.title("Enter IC Number")
    ic_popup.geometry("300x150")
    ic_popup.configure(bg="#D3CAFF")

    Label(ic_popup, text="Enter your IC number:", font=("Arial", 12, "bold"), bg="#D3CAFF").pack(pady=10)
    ic_entry = Entry(ic_popup, font=("Arial", 12))
    ic_entry.pack(pady=5)

    # Button to proceed after entering IC
    proceed_button = ctk.CTkButton(ic_popup, text="Proceed", command=check_ic_and_proceed, font=('Arial', 14),
                                   fg_color="#8387CC", text_color="white", hover_color="#7174AF")
    proceed_button.pack(pady=10)

def ToggleToAdminRegister(event=None):
    # Create a small Toplevel window for admin code input
    admin_code_window = Toplevel()
    admin_code_window.title("Enter Admin Code")
    admin_code_window.geometry("400x200")

    # Label to prompt for the admin code
    lbl_prompt = ctk.CTkLabel(admin_code_window, text="Please enter the Admin Code:", font=('Arial', 14, 'bold'))
    lbl_prompt.pack(pady=20)

    # Entry field to input the admin code
    admin_code_var = ctk.StringVar()
    admin_code_entry = ctk.CTkEntry(admin_code_window, textvariable=admin_code_var, font=('Arial', 14), show="*")
    admin_code_entry.pack(pady=10)

    # Label to display error message
    lbl_error = ctk.CTkLabel(admin_code_window, text="", text_color="red", font=('Arial', 12))
    lbl_error.pack(pady=5)

    # Function to check if the code is correct
    def verify_admin_code():
        admin_code = admin_code_var.get()
        correct_admin_code = "1234"  # Replace with your actual admin code

        if admin_code == correct_admin_code:
            # If the code is correct, destroy the LoginFrame and proceed to AdminRegisterForm
            if LoginFrame is not None:
                LoginFrame.destroy()
            admin_code_window.destroy()  # Close the admin code window
            AdminRegisterForm()  # Redirect to Admin Register Form
        else:
            # If the code is incorrect, display an error message and do not destroy LoginFrame
            lbl_error.configure(text="Incorrect code. Please try again.")

    # Button to submit the admin code using ctk
    btn_submit = ctk.CTkButton(admin_code_window, text="Submit", font=('Arial', 14), command=verify_admin_code,
                               fg_color="#8387CC", text_color="white", hover_color="#7174AF")
    btn_submit.pack(pady=10)

    # Close the window if the admin code is verified or canceled
    admin_code_window.mainloop()

def Register():
    Database()
    tenant = Tenant(conn, cursor)
    admin = Admin(conn, cursor)
    auditor = Auditor(conn, cursor)

    try:
        placeholders = {
            "USERNAME_REGISTER": "Enter your username",
            "PASSWORD_REGISTER": "Enter your password",
            "FULLNAME": "Enter your full name",
            "IC": "Enter your IC",
            "DATE_OF_BIRTH": "Enter day-month-year",
            "EMAIL_ADDRESS": "Enter your email address",
            "PHONE_NUMBER": "Enter your phone number"
        }

        # Check if any field is empty or contains placeholder text
        if (USERNAME_REGISTER.get() in ("", placeholders["USERNAME_REGISTER"]) or
                PASSWORD_REGISTER.get() in ("", placeholders["PASSWORD_REGISTER"]) or
                FULLNAME.get() in ("", placeholders["FULLNAME"]) or
                IC.get() in ("", placeholders["IC"]) or
                confirm_password_entry.get() in ("", placeholders["PASSWORD_REGISTER"]) or
                DATE_OF_BIRTH.get() in ("", placeholders["DATE_OF_BIRTH"]) or
                EMAIL_ADDRESS.get() in ("", placeholders["EMAIL_ADDRESS"]) or
                PHONE_NUMBER.get() in ("", placeholders["PHONE_NUMBER"])):
            messagebox.showerror("Error", "Please complete all the required fields!")
            return

        # Check if the IC format is valid (6 digits - 2 digits - 4 digits)
        ic = IC.get()
        ic_pattern = r"^\d{6}-\d{2}-\d{4}$"
        if not re.match(ic_pattern, ic):
            messagebox.showerror("Error", "IC must be in the format XXXXXX-XX-XXXX (6 digits-2 digits-4 digits)!")
            return

        # Check if the date of birth is valid
        day, month, year = DATE_OF_BIRTH.get().split('-')
        if not is_valid_date(day, month, year):
            messagebox.showerror("Error", "Invalid date of birth!")
            return

        # Check if the username is within the valid length range (6 to 20 characters)
        username = USERNAME_REGISTER.get()
        if not (6 <= len(username) <= 20):
            messagebox.showerror("Error", "Username must be between 6 and 20 characters!")
            return

        # Check if the password is within the valid length range (6 to 20 characters)
        password = PASSWORD_REGISTER.get()
        if not (6 <= len(password) <= 20):
            messagebox.showerror("Error", "Password must be between 6 and 20 characters!")
            return

        # Check if passwords match
        if password != confirm_password_entry.get():
            messagebox.showerror("Error", "Password and Confirm Password do not match!")
            return

        # Validate email format (must end with @gmail.com)
        email = EMAIL_ADDRESS.get()
        if not email.endswith("@gmail.com"):
            messagebox.showerror("Error", "Email must be a valid Gmail address ending with @gmail.com!")
            return

        # Check if the phone number is valid
        phone_number = PHONE_NUMBER.get()
        if not (phone_number.startswith("60") and phone_number.isdigit() and 11 <= len(phone_number) <= 12):
            messagebox.showerror("Error", "Phone number must start with '60' and be 11 to 12 digits long!")
            return

        # Check if the username already exists in tenant or admin tables
        if tenant.get_tenant_by_username(username) or admin.get_admin_by_username(
                username) or auditor.get_auditor_by_username(username):
            messagebox.showerror("Error", "Username is already taken!")
            return

        # Insert the new user into the tenant table
        tenant.register_tenant(username, password, FULLNAME.get(), IC.get(), DATE_OF_BIRTH.get(), email, phone_number)

        # Clear the input fields after successful registration
        USERNAME_REGISTER.set("")
        PASSWORD_REGISTER.set("")
        FULLNAME.set("")
        IC.set("")
        DATE_OF_BIRTH.set("")
        EMAIL_ADDRESS.set("")
        PHONE_NUMBER.set("")
        confirm_password_entry.delete(0, 'end')  # Clear confirm password field

        # Reset the day, month, and year comboboxes
        day_var.set("day")
        month_var.set("month")
        year_var.set("year")

        messagebox.showinfo("Success", "You Successfully Registered. Now, please register your Face ID.")

        # Open Face ID registration window, passing the stored username
        register_face_id(username)

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error occurred during registration: {e}")

def register_face_id(username):
    global face_captured, webcam_label  # Reference the global flag and label
    global cap  # Reference the webcam capture globally

    face_captured = False  # Reset flag when opening registration window
    image_to_save = None
    embedding_to_save = None

    face_id_window = Toplevel()
    face_id_window.title("Face ID Registration")
    face_id_window.configure(bg='#A8B1FF')

    lbl_title = Label(face_id_window, text="Face ID Registration",
                      font=('Bernard MT Condensed', 20, 'bold'), bg='#A8B1FF')
    lbl_title.pack(pady=10)
    lbl_instruction = Label(face_id_window, text="Click 'Start' to begin Face ID registration.", font=('arial', 12),
                            bg='#A8B1FF')
    lbl_instruction.pack(pady=10)

    # Label for webcam feed
    webcam_label = Label(face_id_window, bg='#A8B1FF')
    webcam_label.pack(pady=10)

    start_button = ctk.CTkButton(face_id_window, text="Start",
                                 command=lambda: start_webcam_capture(username, face_id_window, start_button,
                                                                      save_button),
                                 font=('times new roman', 22, 'bold'), fg_color='#16417C', text_color='white',
                                 corner_radius=50)
    start_button.bind("<Enter>", lambda e: start_button.configure(fg_color="#256ED1"))
    start_button.bind("<Leave>", lambda e: start_button.configure(fg_color="#16417C"))
    start_button.pack(pady=10)

    # Disable 'Save' button by default
    save_button = ctk.CTkButton(face_id_window, text="Capture", state="disabled",
                                command=lambda: capture_and_save_face(username, face_id_window, save_button),
                                font=('times new roman', 22, 'bold'), fg_color='#16417C', text_color='white',
                                corner_radius=50)
    save_button.bind("<Enter>", lambda e: save_button.configure(fg_color="#256ED1"))
    save_button.bind("<Leave>", lambda e: save_button.configure(fg_color="#16417C"))
    save_button.pack(pady=10)

    # Function to update webcam feed in the Label widget
    def show_frame():
        ret, frame = cap.read()
        if ret:
            # Convert the image to RGB and then to a format compatible with Tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)

            # Update the webcam feed label with the new frame
            webcam_label.imgtk = imgtk
            webcam_label.config(image=imgtk)

            # Continue to capture the next frame
            face_id_window.after(10, show_frame)

    # Start the webcam and display the feed
    def start_webcam_capture(username, face_id_window, start_button, save_button):
        global cap  # Webcam capture object
        cap = cv2.VideoCapture(0)  # Open the webcam
        if not cap.isOpened():
            messagebox.showerror("Error", "Could not open webcam.")
            return

        start_button.configure(state="disabled")  # Disable Start button
        save_button.configure(state="normal")  # Enable Save button
        show_frame()  # Start showing the webcam feed

    # Capture and save the face ID when Save button is clicked
    def capture_and_save_face(username, face_id_window, save_button):
        global image_to_save, embedding_to_save

        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Error", "Failed to capture frame.")
            return

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        try:
            # Find face locations and encode the face in the image
            face_locations = face_recognition.face_locations(frame_rgb)
            if not face_locations:
                messagebox.showerror("Error", "No face detected in the frame.")
                return

            # Extract the face embeddings
            face_encodings = face_recognition.face_encodings(frame_rgb, face_locations)
            if not face_encodings:
                messagebox.showerror("Error", "No face encoding found.")
                return

            # Save the image and embedding
            image_to_save = frame
            embedding_to_save = face_encodings[0]

            # Save the image and embedding to the database
            save_face_id(face_id_window, username)

        except Exception as e:
            messagebox.showerror("Error", f"Face could not be detected: {e}")

    # Save the captured face ID into the database
    def save_face_id(face_id_window, username):
        global image_to_save, embedding_to_save

        try:
            if embedding_to_save is not None and image_to_save is not None:
                # Define file path and name
                image_filename = f"face_id_{username}.png"

                # Save the image
                if cv2.imwrite(image_filename, image_to_save):
                    print(f"Image saved successfully as {image_filename}")
                else:
                    raise IOError("Failed to save the image file.")

                # Convert embedding to bytes
                embedding_bytes = embedding_to_save.tobytes()

                # Check if the username belongs to a tenant or admin
                cursor.execute("SELECT COUNT(*) FROM tenant WHERE username = ?", (username,))
                if cursor.fetchone()[0] > 0:
                    # Update tenant table
                    cursor.execute(
                        "UPDATE tenant SET face_id_image = ?, face_embedding = ? WHERE username = ?",
                        (image_filename, embedding_bytes, username)
                    )
                else:
                    cursor.execute("SELECT COUNT(*) FROM admin WHERE username = ?", (username,))
                    if cursor.fetchone()[0] > 0:
                        # Update admin table
                        cursor.execute(
                            "UPDATE admin SET face_id_image = ?, face_embedding = ? WHERE username = ?",
                            (image_filename, embedding_bytes, username)
                        )
                    else:
                        cursor.execute("SELECT COUNT(*) FROM auditor WHERE username = ?", (username,))
                        if cursor.fetchone()[0] > 0:
                            # Update auditor table
                            cursor.execute(
                                "UPDATE auditor SET face_id_image = ?, face_embedding = ? WHERE username = ?",
                                (image_filename, embedding_bytes, username)
                            )
                        else:
                            raise ValueError("Username does not exist for tenant, admin, or auditor.")

                conn.commit()
                print("Database updated successfully")
                messagebox.showinfo("Success", "Face ID saved successfully!")

                # Close webcam and destroy window
                cap.release()
                face_id_window.destroy()
            else:
                messagebox.showerror("Error", "No Face ID captured. Please start the capture process again.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")
            print(f"Error details: {e}")
        finally:
            # Clear the global variables
            embedding_to_save = None
            image_to_save = None

def auditor_account(ic_number=None):
    global confirm_password_entry, password_entry, auditor_openEye_button, auditor_confirm_openEye_button
    global auditor_openEye_status, auditor_confirm_openEye_status, auditor_openEyeButton_image, auditor_closeEyeButton_image
    global USERNAME_REGISTER, PASSWORD_REGISTER, FULLNAME, IC, EMAIL_ADDRESS, PHONE_NUMBER, DATE_OF_BIRTH, day_var, month_var, year_var
    global AuditorFrame
    global entered_code

    root.withdraw()

    AuditorFrame = Frame(form_frame, highlightbackground="black", highlightcolor="black", highlightthickness=2)
    AuditorFrame.pack(side='top', pady=(60, 20))

    lbl_login = Label(AuditorFrame, text="Click to Login", fg="#00A4FF", font=('arial', 12))
    lbl_login.bind('<Enter>', lambda event, label=lbl_login: label.config(font=('arial', 12, 'underline')))
    lbl_login.bind('<Leave>', lambda event, label=lbl_login: label.config(font=('arial', 12)))
    lbl_login.grid(row=12, columnspan=4, pady=5)
    lbl_login.bind('<Button-1>', ToggleToAuditor)

    lbl_result = Label(AuditorFrame, text="Auditor Registration Form:", font=('times new roman', 24, 'bold'),
                       fg='#0016BA', bd=18)
    lbl_result.grid(row=1, columnspan=4)

    # Labels for each entry field
    lbl_username = Label(AuditorFrame, text="Username:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_username.grid(row=2)

    lbl_password = Label(AuditorFrame, text="Password:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_password.grid(row=3)

    lbl_confirm_password = Label(AuditorFrame, text="Confirm Password:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_confirm_password.grid(row=4)

    lbl_fullname = Label(AuditorFrame, text="Full Name:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_fullname.grid(row=5)

    lbl_ic = Label(AuditorFrame, text="IC:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_ic.grid(row=6)

    lbl_date_of_birth = Label(AuditorFrame, text="Date of Birth:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_date_of_birth.grid(row=7)

    lbl_email_address = Label(AuditorFrame, text="Email Address:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_email_address.grid(row=8)

    lbl_phone_number = Label(AuditorFrame, text="Phone Number:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_phone_number.grid(row=9)

    # Clear existing text in the entry fields
    USERNAME_REGISTER.set("")
    PASSWORD_REGISTER.set("")
    FULLNAME.set("")
    EMAIL_ADDRESS.set("")
    PHONE_NUMBER.set("")
    DATE_OF_BIRTH = StringVar()
    entered_code = StringVar()

    # Entry fields with placeholders
    username_entry = Entry(AuditorFrame, font=('times new roman', 15), width=20, textvariable=USERNAME_REGISTER,
                           highlightbackground="black", highlightcolor="black", highlightthickness=1)
    username_entry.grid(row=2, column=1, padx=10)
    username_entry.insert(0, "Enter username")
    username_entry.config(fg='grey')
    username_entry.bind("<FocusIn>", lambda event: on_entry_click(username_entry, "Enter username"))
    username_entry.bind("<FocusOut>", lambda event: on_focus_out(username_entry, "Enter username"))

    password_entry = Entry(AuditorFrame, font=('times new roman', 15), width=20, textvariable=PASSWORD_REGISTER,
                           highlightbackground="black", highlightcolor="black", highlightthickness=1)
    password_entry.grid(row=3, column=1, padx=10)
    password_entry.insert(0, "Enter password")
    password_entry.config(fg='grey')
    password_entry.bind("<FocusIn>", lambda event: password_on_focus_in(password_entry, "Enter password"))
    password_entry.bind("<FocusOut>", lambda event: password_on_focus_out(password_entry, "Enter password"))
    password_entry.bind("<KeyRelease>", lambda event: auditor_check_password_field_register())

    confirm_password_entry = Entry(AuditorFrame, font=('times new roman', 15), width=20, highlightbackground="black",
                                   highlightcolor="black", highlightthickness=1)
    confirm_password_entry.grid(row=4, column=1, padx=10)
    confirm_password_entry.insert(0, "Confirm password")
    confirm_password_entry.config(fg='grey')
    confirm_password_entry.bind("<FocusIn>",
                                lambda event: password_on_focus_in(confirm_password_entry, "Confirm password"))
    confirm_password_entry.bind("<FocusOut>",
                                lambda event: password_on_focus_out(confirm_password_entry, "Confirm password"))
    confirm_password_entry.bind("<KeyRelease>", lambda event: auditor_check_confirm_password_field_register())

    # Eye buttons for password visibility toggle
    auditor_openEyeButton_image = ImageTk.PhotoImage(Image.open("image\\open_eye.png").resize((20, 20)))
    auditor_closeEyeButton_image = ImageTk.PhotoImage(Image.open("image\\closed_eye.png").resize((20, 20)))

    auditor_openEye_button = Button(AuditorFrame, image=auditor_closeEyeButton_image,
                                    command=auditor_show_password_register)
    auditor_openEye_button.grid(row=3, column=2, padx=5)
    auditor_openEye_button.config(state='disabled')

    auditor_openEye_status = Label(AuditorFrame, text='Close')
    auditor_openEye_status.grid(row=3, column=3)
    auditor_openEye_status.grid_remove()

    auditor_confirm_openEye_button = Button(AuditorFrame, image=auditor_closeEyeButton_image,
                                            command=auditor_show_confirm_password_register)
    auditor_confirm_openEye_button.grid(row=4, column=2, padx=5)
    auditor_confirm_openEye_button.config(state='disabled')

    auditor_confirm_openEye_status = Label(AuditorFrame, text='Close')
    auditor_confirm_openEye_status.grid(row=4, column=3)
    auditor_confirm_openEye_status.grid_remove()

    fullname_entry = Entry(AuditorFrame, font=('times new roman', 15), width=20, textvariable=FULLNAME,
                           highlightbackground="black", highlightcolor="black", highlightthickness=1)
    fullname_entry.grid(row=5, column=1, padx=10)
    fullname_entry.insert(0, "Enter full name")
    fullname_entry.config(fg='grey')
    fullname_entry.bind("<FocusIn>", lambda event: on_entry_click(fullname_entry, "Enter full name"))
    fullname_entry.bind("<FocusOut>", lambda event: on_focus_out(fullname_entry, "Enter full name"))

    # Configure IC entry field to be pre-filled and readonly
    IC.set(ic_number)  # Set the provided IC number
    ic = Entry(AuditorFrame, font=('times new roman', 15), textvariable=IC, width=20, highlightbackground="black",
               highlightcolor="black", highlightthickness=1, state="readonly")
    ic.grid(row=6, column=1, padx=10)

    # Create Date of Birth dropdowns
    setup_combobox_styles()

    day_var = StringVar(AuditorFrame)
    month_var = StringVar(AuditorFrame)
    year_var = StringVar(AuditorFrame)

    days = [str(i).zfill(2) for i in range(1, 32)]
    months = [str(i).zfill(2) for i in range(1, 13)]
    current_year = datetime.datetime.now().year
    years = [str(i) for i in range(current_year, 1899, -1)]

    day_menu = ttk.Combobox(AuditorFrame, textvariable=day_var, values=days, width=8, state="readonly",
                            style='TCombobox')
    day_menu.grid(row=7, column=1, sticky="w", padx=10)
    day_menu.set("day")

    month_menu = ttk.Combobox(AuditorFrame, textvariable=month_var, values=months, width=8, state="readonly",
                              style='TCombobox')
    month_menu.grid(row=7, column=1)
    month_menu.set("month")

    year_menu = ttk.Combobox(AuditorFrame, textvariable=year_var, values=years, width=8, state="readonly",
                             style='TCombobox')
    year_menu.grid(row=7, column=1, sticky="e", padx=10)
    year_menu.set("year")

    # Store the selected date of birth in the DATE_OF_BIRTH variable
    def update_dob():
        if day_var.get() != "day" and month_var.get() != "month" and year_var.get() != "year":
            DATE_OF_BIRTH.set(f"{day_var.get()}-{month_var.get()}-{year_var.get()}")
        else:
            DATE_OF_BIRTH.set("")

    day_var.trace("w", lambda *args: update_dob())
    month_var.trace("w", lambda *args: update_dob())
    year_var.trace("w", lambda *args: update_dob())

    email_entry = Entry(AuditorFrame, font=('times new roman', 15), width=20, textvariable=EMAIL_ADDRESS,
                        highlightbackground="black", highlightcolor="black", highlightthickness=1)
    email_entry.grid(row=8, column=1, padx=10)
    email_entry.insert(0, "Enter email address")
    email_entry.config(fg='grey')
    email_entry.bind("<FocusIn>", lambda event: on_entry_click(email_entry, "Enter email address"))
    email_entry.bind("<FocusOut>", lambda event: on_focus_out(email_entry, "Enter email address"))

    phone_entry = Entry(AuditorFrame, font=('times new roman', 15), width=20, textvariable=PHONE_NUMBER,
                        highlightbackground="black", highlightcolor="black", highlightthickness=1)
    phone_entry.grid(row=9, column=1, padx=10)
    phone_entry.insert(0, "Enter phone number")
    phone_entry.config(fg='grey')
    phone_entry.bind("<FocusIn>", lambda event: on_entry_click(phone_entry, "Enter phone number"))
    phone_entry.bind("<FocusOut>", lambda event: on_focus_out(phone_entry, "Enter phone number"))

    # Add a button to send the verification code to the user's email
    btn_send_code = ctk.CTkButton(AuditorFrame, text="get code", font=('times new roman', 15, 'bold'), width=15,
                                  command=lambda: send_verification_email(EMAIL_ADDRESS), corner_radius=50)
    btn_send_code.grid(row=10, column=2, padx=5)

    # Add a field for the user to enter the verification code
    lbl_verification_code = Label(AuditorFrame, text="Verification Code:", font=('times new roman', 15, 'bold'), bd=18)
    lbl_verification_code.grid(row=10, column=0)

    verification_code_entry = Entry(AuditorFrame, textvariable=entered_code, font=('times new roman', 15), width=20,
                                    highlightbackground="black", highlightcolor="black", highlightthickness=1)
    verification_code_entry.insert(0, "Enter verification code")
    verification_code_entry.config(fg='grey')
    verification_code_entry.bind("<FocusIn>",
                                 lambda event: on_entry_click(verification_code_entry, "Enter verification code"))
    verification_code_entry.bind("<FocusOut>",
                                 lambda event: on_focus_out(verification_code_entry, "Enter verification code"))
    verification_code_entry.grid(row=10, column=1, padx=10)

    # Button to register the auditor
    btn_register = ctk.CTkButton(AuditorFrame, text="Register", font=('times new roman', 22, 'bold'),
                                 fg_color='#A5AAF7',
                                 text_color='white', corner_radius=50, command=verify_code_input_auditor)
    btn_register.grid(row=11, columnspan=3, pady=5)

def ToggleToAuditorRegister(event=None):
    def check_ic_and_proceed():
        ic = ic_entry.get().strip()

        if ic:
            try:
                # Query to check if the IC exists in the auditor table
                cursor.execute("SELECT * FROM auditor WHERE ic = ?", (ic,))
                existing_auditor = cursor.fetchone()

                if existing_auditor:
                    auditor_id, username, password, fullname, ic, date_of_birth, email_address, phone_number, face_id_image, face_embedding = existing_auditor

                    if any(field is None for field in
                           [username, password, fullname, date_of_birth, email_address, phone_number]):
                        messagebox.showinfo("Registration Required", "Please complete your registration.")
                        ic_popup.destroy()
                        auditor_account(ic_number=ic)  # Pass the IC number to the registration form
                    else:
                        messagebox.showinfo("Account Exists", "You already have an account.")
                        ic_popup.destroy()
                else:
                    messagebox.showerror("Error", "IC number not found. Please check your entry.")
                    ic_popup.destroy()

            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Database error: {e}")
                ic_popup.destroy()
        else:
            messagebox.showwarning("Warning", "Please enter your IC number.")

    # Create a popup to enter IC number
    ic_popup = Toplevel()
    ic_popup.title("Enter IC Number")
    ic_popup.geometry("300x150")
    ic_popup.configure(bg="#D3CAFF")

    Label(ic_popup, text="Enter your IC number:", font=("Arial", 12, "bold"), bg="#D3CAFF").pack(pady=10)
    ic_entry = Entry(ic_popup, font=("Arial", 12))
    ic_entry.pack(pady=5)

    # Button to proceed after entering IC
    proceed_button = ctk.CTkButton(ic_popup, text="Proceed", command=check_ic_and_proceed, font=('Arial', 14),
                                   fg_color="#8387CC", text_color="white", hover_color="#7174AF")
    proceed_button.pack(pady=10)

def ToggleToAuditor(event=None):
    if AuditorFrame is not None:
        form_frame.withdraw()
        AuditorFrame.destroy()
    # Clear any previous text and animation before switching forms
    canvas.delete("text")  # Clear any text on the canvas
    animate_text()  # Start the text animation
    LoginForm()

def auditor_is_valid_date(day, month, year):
    from datetime import datetime

    try:
        datetime(int(year), int(month), int(day))
        return True
    except ValueError:
        return False

def auditor_check_password_field_register():
    if password_entry.get() == "" or password_entry.get() == "Enter auditor password":
        auditor_openEye_button.config(state='disabled')
    else:
        auditor_openEye_button.config(state='normal')

def auditor_check_confirm_password_field_register():
    if confirm_password_entry.get() == "" or confirm_password_entry.get() == "Confirm auditor password":
        auditor_confirm_openEye_button.config(state='disabled')
    else:
        auditor_confirm_openEye_button.config(state='normal')

def auditor_show_password_register():
    if auditor_openEye_status.cget('text') == 'Close':
        auditor_openEye_button.configure(image=openEyeButton_image)
        password_entry.config(show='')  # Show the password
        auditor_openEye_status.configure(text='Open')
    elif auditor_openEye_status.cget('text') == 'Open':
        auditor_openEye_button.configure(image=closeEyeButton_image)
        password_entry.config(show='*')  # Hide the password
        auditor_openEye_status.configure(text='Close')

def auditor_show_confirm_password_register():
    if auditor_confirm_openEye_status.cget('text') == 'Close':
        auditor_confirm_openEye_button.configure(image=openEyeButton_image)
        confirm_password_entry.config(show='')  # Show the password
        auditor_confirm_openEye_status.configure(text='Open')
    elif auditor_confirm_openEye_status.cget('text') == 'Open':
        auditor_confirm_openEye_button.configure(image=closeEyeButton_image)
        confirm_password_entry.config(show='*')  # Hide the password
        auditor_confirm_openEye_status.configure(text='Close')

def register_auditor():
    Database()
    auditor = Auditor(conn, cursor)
    tenant = Tenant(conn, cursor)
    admin = Admin(conn, cursor)

    try:
        placeholders = {
            "USERNAME_REGISTER": "Enter username",
            "PASSWORD_REGISTER": "Enter password",
            "FULLNAME": "Enter full name",
            "IC": "Enter IC",
            "DATE_OF_BIRTH": "Enter day-month-year",
            "EMAIL_ADDRESS": "Enter email address",
            "PHONE_NUMBER": "Enter phone number"
        }

        # Check if any field is empty or contains placeholder text
        if (USERNAME_REGISTER.get() in ("", placeholders["USERNAME_REGISTER"]) or
                PASSWORD_REGISTER.get() in ("", placeholders["PASSWORD_REGISTER"]) or
                FULLNAME.get() in ("", placeholders["FULLNAME"]) or
                IC.get() in ("", placeholders["IC"]) or
                confirm_password_entry.get() in ("", placeholders["PASSWORD_REGISTER"]) or
                DATE_OF_BIRTH.get() in ("", placeholders["DATE_OF_BIRTH"]) or
                EMAIL_ADDRESS.get() in ("", placeholders["EMAIL_ADDRESS"]) or
                PHONE_NUMBER.get() in ("", placeholders["PHONE_NUMBER"])):
            messagebox.showerror("Error", "Please complete all the required fields!")
            return

        # Check if the IC format is valid (6 digits - 2 digits - 4 digits)
        ic = IC.get()
        ic_pattern = r"^\d{6}-\d{2}-\d{4}$"
        if not re.match(ic_pattern, ic):
            messagebox.showerror("Error", "IC must be in the format XXXXXX-XX-XXXX (6 digits-2 digits-4 digits)!")
            return

        # Check if the date of birth is valid
        day, month, year = DATE_OF_BIRTH.get().split('-')
        if not auditor_is_valid_date(day, month, year):
            messagebox.showerror("Error", "Invalid date of birth!")
            return

        # Check if the username is within the valid length range (6 to 20 characters)
        username = USERNAME_REGISTER.get()
        if not (6 <= len(username) <= 20):
            messagebox.showerror("Error", "Username must be between 6 and 20 characters!")
            return

        # Check if the password is within the valid length range (6 to 20 characters)
        password = PASSWORD_REGISTER.get()
        if not (6 <= len(password) <= 20):
            messagebox.showerror("Error", "Password must be between 6 and 20 characters!")
            return

        # Check if passwords match
        if password != confirm_password_entry.get():
            messagebox.showerror("Error", "Password and Confirm Password do not match!")
            return

        # Validate email format (must end with @gmail.com)
        email = EMAIL_ADDRESS.get()
        if not email.endswith("@gmail.com"):
            messagebox.showerror("Error", "Email must be a valid Gmail address ending with @gmail.com!")
            return

        # Check if the phone number is valid
        phone_number = PHONE_NUMBER.get()
        if not (phone_number.startswith("60") and phone_number.isdigit() and 11 <= len(phone_number) <= 12):
            messagebox.showerror("Error", "Phone number must start with '60' and be 11 to 12 digits long!")
            return

        # Check if the username already exists in the auditor table
        if auditor.get_auditor_by_username(username) or tenant.get_tenant_by_username(
                username) or admin.get_admin_by_username(username):
            messagebox.showerror("Error", "Username is already taken!")
            return

        # Insert the new user into the auditor table
        auditor.register_or_update_auditor(username, password, FULLNAME.get(), IC.get(), DATE_OF_BIRTH.get(), email,
                                           phone_number)

        # Clear the input fields after successful registration
        USERNAME_REGISTER.set("")
        PASSWORD_REGISTER.set("")
        FULLNAME.set("")
        IC.set("")
        DATE_OF_BIRTH.set("")
        EMAIL_ADDRESS.set("")
        PHONE_NUMBER.set("")
        confirm_password_entry.delete(0, 'end')  # Clear confirm password field

        # Reset the day, month, and year comboboxes
        day_var.set("day")
        month_var.set("month")
        year_var.set("year")

        messagebox.showinfo("Success", "Auditor Successfully Registered. ")
        # Open Face ID registration window, passing the stored username
        register_face_id(username)
    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error occurred during registration: {e}")

def Login():
    global logged_in_user
    Database()
    try:
        # Check if the fields are empty
        if USERNAME_LOGIN.get() == "" or PASSWORD_LOGIN.get() == "":
            messagebox.showerror("Error", "Please complete the required field!")
            return

        # Create an instance of the Tenant class
        tenant_instance = Tenant(conn, cursor)

        # Check in the tenant table using the new method
        tenant = tenant_instance.get_tenant_by_credentials(USERNAME_LOGIN.get(), PASSWORD_LOGIN.get())

        if tenant is not None:
            logged_in_user['username'] = USERNAME_LOGIN.get()
            logged_in_user['password'] = PASSWORD_LOGIN.get()
            messagebox.showinfo("Success", "You Successfully Logged In")
            tenant_dashboard()
            return

        # Create an instance of the Admin class
        admin_instance = Admin(conn, cursor)

        # Check in the admin table using the new method
        admin = admin_instance.get_admin_by_credentials(USERNAME_LOGIN.get(), PASSWORD_LOGIN.get())

        if admin is not None:
            logged_in_user['username'] = USERNAME_LOGIN.get()
            logged_in_user['password'] = PASSWORD_LOGIN.get()
            messagebox.showinfo("Success", "You Successfully Logged In")
            admin_dashboard()
            return

        # Create an instance of the Auditor class
        auditor_instance = Auditor(conn, cursor)

        # Check in the auditor table using the new method
        auditor = auditor_instance.get_auditor_by_credentials(USERNAME_LOGIN.get(), PASSWORD_LOGIN.get())

        if auditor is not None:
            logged_in_user['username'] = USERNAME_LOGIN.get()
            logged_in_user['password'] = PASSWORD_LOGIN.get()
            messagebox.showinfo("Success", "You Successfully Logged In")
            auditor_dashboard()  # Replace with the appropriate function for auditor dashboard
            return

        # If no match found in all tables
        messagebox.showerror("Error", "Invalid username or password")

    except sqlite3.Error as e:
        messagebox.showerror("Error", f"Error occurred during login: {e}")

def load_window():
    try:
        # Try to load the image
        image = Image.open('image\\name.png')

        # Resize the image
        resized_image = image.resize((500, 500), Image.Resampling.LANCZOS)

        # Convert the image to a format suitable for Tkinter
        bg_image = ImageTk.PhotoImage(resized_image)
    except Exception as e:
        # Show an error message and exit if the image could not be loaded
        messagebox.showerror("Image Error", f"Could not load image: {e}")
        root.destroy()  # Close the application
        return  # Exit the function

    # Create a canvas with the background image and place it on the window
    canvas = Canvas(root, width=500, height=500, highlightbackground="black", highlightcolor="black",
                    highlightthickness=2)
    canvas.create_image(0, 0, anchor='nw', image=bg_image)
    canvas.place(x=0, y=0, relwidth=1, relheight=1)

    # Update the window's geometry to fit the image
    width, height = resized_image.size
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    root.overrideredirect(True)  # Remove window decorations
    root.resizable(False, False)  # Make the window non-resizable

    # Set the background color to match the yellow border
    root.config(background="#f1c40f")

    # Add a welcome text to the canvas with more space and centered on two lines
    canvas.create_text(width // 2, 50, text="WELCOME TO\nGOVERNMENT STALL RENTAL SYSTEM!",
                       font=("Bernard MT Condensed", 20, "bold"), fill="#FFFFFF", width=400, justify="center")

    # Add a progress label to the canvas
    progress_text = canvas.create_text(width // 2, height - 70, text="Loading...",
                                       font=("Bernard MT Condensed", 15, "bold"), fill="#FFFFFF")

    # Configure the progress bar style
    style = Style()
    style.theme_use('clam')
    style.configure("red.Horizontal.TProgressbar", background="#108cff")

    # Add the progress bar (we cannot use canvas for progressbar)
    progress = Progressbar(root, orient='horizontal', length=400, mode='determinate',
                           style="red.Horizontal.TProgressbar")
    progress.place(x=(width - 400) // 2, y=height - 40)  # Place near the bottom

    def top():
        # Close the current window and open the LandingPage
        root.withdraw()
        root.destroy()

    def load():
        # Simulate a loading process
        global i
        if i <= 100:
            txt = 'Loading...' + (str(i) + '%')
            canvas.itemconfig(progress_text, text=txt)
            progress['value'] = i
            i += 1
            canvas.after(60, load)  # Call this function again after 60 milliseconds
        else:
            LoginForm()

    # Start the loading process
    load()

    # Keep a reference to the image object to prevent garbage collection
    load_window.image = bg_image


# Initialize the global variable
i = 0

# Call the function to load the window
load_window()

Database()

schedule_rental_check()

check_all_attendance_and_notify()

# Schedule this function to run daily
check_overdue_payments()

if __name__ == '__main__':
    root.mainloop()