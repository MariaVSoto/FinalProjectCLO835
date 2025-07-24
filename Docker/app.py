# app.py
from flask import Flask, render_template, request
import pymysql
import os
import boto3

app = Flask(__name__)

# Environment Variables

DB_HOST = os.environ.get("DBHOST")
DB_USER = os.environ.get("DBUSER")
DB_PASSWORD = os.environ.get("DBPWD")
DB_NAME = os.environ.get("DATABASE")
DB_PORT = int(os.environ.get("DBPORT", 3306))

# S3 & Background Image Config
S3_BUCKET = os.environ.get('S3_BUCKET')
S3_KEY = os.environ.get('S3_KEY') 
S3_REGION = os.environ.get('AWS_REGION', 'us-east-1')

# AWS Credentials for S3
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_SESSION_TOKEN = os.environ.get('AWS_SESSION_TOKEN')

# Group Info 
GROUP_NAME = os.environ.get('GROUP_NAME', 'Shruti and Maria')
SLOGAN = os.environ.get('SLOGAN', 'Automating the Cloud, One Pod at a Time!')

# Improved Database Connection Handling

def get_db_connection():
    """Creates a database connection using PyMySQL."""
    try:
        connection = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=5
        )
        print("Database connection successful!")
        return connection
    except pymysql.MySQLError as e:
        print(f"Error connecting to MySQL Database: {e}")
        return None

# S3 Image Download Function ---
def download_background_image():
    """Downloads the background image from a private S3 bucket to the static folder."""
    if not all([S3_BUCKET, S3_KEY, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_SESSION_TOKEN]):
        print("S3 environment variables not fully configured. Skipping download.")
        return "default.jpg" 

    if not os.path.exists('static'):
        os.makedirs('static')

    image_local_path = os.path.join('static', S3_KEY)
    
    # Log the background image URL
    s3_url = f"s3://{S3_BUCKET}/{S3_KEY}"
    print(f"Attempting to download background image from: {s3_url}")
    
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=S3_REGION,
            aws_session_token=AWS_SESSION_TOKEN
        )
        s3_client.download_file(S3_BUCKET, S3_KEY, image_local_path)
        print(f"Successfully downloaded image to {image_local_path}")
        return S3_KEY 
    except Exception as e:
        print(f"Error downloading from S3: {e}")
        return "default.jpg" 

# --- UPDATED: Your Existing Routes ---

@app.route("/", methods=['GET', 'POST'])
def home():
    # Call the download function for every page render
    bg_image_filename = download_background_image()
    return render_template(
        'addemp.html', 
        group_name=GROUP_NAME, 
        slogan=SLOGAN,
        background_image_filename=bg_image_filename
    )

@app.route("/about", methods=['GET','POST'])
def about():
    bg_image_filename = download_background_image()
    return render_template(
        'about.html', 
        group_name=GROUP_NAME, 
        slogan=SLOGAN,
        background_image_filename=bg_image_filename
    )
    
@app.route("/addemp", methods=['POST'])
def AddEmp():
    bg_image_filename = download_background_image()
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    primary_skill = request.form['primary_skill']
    location = request.form['location']
  
    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    connection = get_db_connection()
    if not connection:
        return "Database connection failed", 500

    try:
        with connection.cursor() as cursor:
            cursor.execute(insert_sql, (emp_id, first_name, last_name, primary_skill, location))
        connection.commit()
        emp_name = f"{first_name} {last_name}"
    except Exception as e:
        print(f"Error during DB insert: {e}")
        return "Error inserting data", 500
    finally:
        connection.close()

    print("Employee added successfully.")
    return render_template(
        'addempoutput.html', 
        name=emp_name, 
        group_name=GROUP_NAME, 
        slogan=SLOGAN,
        background_image_filename=bg_image_filename
    )

@app.route("/getemp", methods=['GET', 'POST'])
def GetEmp():
    bg_image_filename = download_background_image()
    return render_template(
        "getemp.html", 
        group_name=GROUP_NAME, 
        slogan=SLOGAN,
        background_image_filename=bg_image_filename
    )

@app.route("/fetchdata", methods=['POST'])
def FetchData():
    bg_image_filename = download_background_image()
    emp_id = request.form['emp_id']

    output = {}
    select_sql = "SELECT emp_id, first_name, last_name, primary_skill, location from employee where emp_id=%s"
    connection = get_db_connection()
    if not connection:
        return "Database connection failed", 500

    try:
        with connection.cursor() as cursor:
            cursor.execute(select_sql, (emp_id,))
            result = cursor.fetchone()
        
        if result:
            output = result
        else:
            # Handle case where employee is not found gracefully
            return render_template("getempoutput.html", error="Employee not found", group_name=GROUP_NAME, slogan=SLOGAN, background_image_filename=bg_image_filename)
            
    except Exception as e:
        print(f"Error during DB fetch: {e}")
        return "Error fetching data", 500
    finally:
        connection.close()

    return render_template(
        "getempoutput.html", 
        id=output.get("emp_id"), 
        fname=output.get("first_name"),
        lname=output.get("last_name"), 
        interest=output.get("primary_skill"), 
        location=output.get("location"),
        group_name=GROUP_NAME, 
        slogan=SLOGAN,
        background_image_filename=bg_image_filename
    )

# Main run block ---
if __name__ == '__main__':
    
    app.run(host='0.0.0.0', port=81)
