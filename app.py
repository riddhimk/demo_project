import streamlit as st
import mysql.connector
import pandas as pd
from mysql.connector import Error

# Establish connection to the MySQL database
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='riddhim10000',
            database='PC_BUILD'
        )
        if connection.is_connected():
            return connection
        else:
            st.error("Failed to connect to the database")
            return None
    except Error as e:
        st.error(f"Error connecting to the database: {e}")
        return None

# Ensure the connection is closed properly
def close_connection(connection):
    if connection and connection.is_connected():
        connection.close()

def register_user(username, password):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM USERS WHERE USERNAME = %s", (username,))
            if cursor.fetchone():
                st.error("Username already exists. Please choose another.")
            else:
                cursor.execute("INSERT INTO USERS (USERNAME, PASSWORD) VALUES (%s, %s)", (username, password))
                connection.commit()
                st.success("Registration successful. Please log in.")
        except Error as e:
            st.error(f"Error occurred: {e}")
        finally:
            cursor.close()
            close_connection(connection)

def login_user(username, password):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM USERS WHERE USERNAME = %s AND PASSWORD = %s", (username, password))
            return cursor.fetchone() is not None
        except Error as e:
            st.error(f"Error occurred during login: {e}")
            return False
        finally:
            cursor.close()
            close_connection(connection)

def view_existing_builds():
    connection = create_connection()
    if connection:
        try:
            query = """
            SELECT pc.BUILD_ID, cpu.BRAND AS CPU_BRAND, cpu.MODEL AS CPU_MODEL, gpu.BRAND AS GPU_BRAND, gpu.MODEL AS GPU_MODEL,
                   ram.BRAND AS RAM_BRAND, ram.CAPACITY AS RAM_CAPACITY, ps.BRAND AS PSU_BRAND, ps.WATTAGE AS PSU_WATTAGE,
                   mon.BRAND AS MONITOR_BRAND, mon.SIZE AS MONITOR_SIZE, mb.BRAND AS MB_BRAND, strg.BRAND AS STORAGE_BRAND,
                   strg.TYPE AS STORAGE_TYPE, strg.CAPACITY AS STORAGE_CAPACITY, pc.TOTAL_PRICE
            FROM PC_BUILD pc
            JOIN CPU cpu ON pc.CPU_ID = cpu.CPU_ID
            JOIN GPU gpu ON pc.GPU_ID = gpu.GPU_ID
            JOIN RAM ram ON pc.RAM_ID = ram.RAM_ID
            JOIN POWER_SUPPLY ps ON pc.PSU_ID = ps.PSU_ID
            JOIN MONITOR mon ON pc.MON_ID = mon.MON_ID
            JOIN MOTHERBOARD mb ON pc.MB_ID = mb.MB_ID
            JOIN STORAGE strg ON pc.STR_ID = strg.STR_ID
            """
            df = pd.read_sql(query, connection)
            st.dataframe(df)
        except Error as e:
            st.error(f"Error retrieving builds: {e}")
        finally:
            close_connection(connection)

def add_new_build():
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            st.write("Select components for the new build:")

            # Fetch component details
            cpu_df = pd.read_sql("SELECT * FROM CPU", connection)
            gpu_df = pd.read_sql("SELECT * FROM GPU", connection)
            ram_df = pd.read_sql("SELECT * FROM RAM", connection)
            psu_df = pd.read_sql("SELECT * FROM POWER_SUPPLY", connection)
            mon_df = pd.read_sql("SELECT * FROM MONITOR", connection)
            mb_df = pd.read_sql("SELECT * FROM MOTHERBOARD", connection)
            strg_df = pd.read_sql("SELECT * FROM STORAGE", connection)

            # Display components and allow user to select
            st.write("### CPU")
            st.dataframe(cpu_df)
            cpu_id = st.number_input("Enter CPU ID:", min_value=1, step=1)

            st.write("### GPU")
            st.dataframe(gpu_df)
            gpu_id = st.number_input("Enter GPU ID:", min_value=1, step=1)

            st.write("### RAM")
            st.dataframe(ram_df)
            ram_id = st.number_input("Enter RAM ID:", min_value=1, step=1)

            st.write("### Power Supply")
            st.dataframe(psu_df)
            psu_id = st.number_input("Enter PSU ID:", min_value=1, step=1)

            st.write("### Monitor")
            st.dataframe(mon_df)
            mon_id = st.number_input("Enter Monitor ID:", min_value=1, step=1)

            st.write("### Motherboard")
            st.dataframe(mb_df)
            mb_id = st.number_input("Enter Motherboard ID:", min_value=1, step=1)

            st.write("### Storage")
            st.dataframe(strg_df)
            str_id = st.number_input("Enter Storage ID:", min_value=1, step=1)

            if st.button("Add Build"):
                # Calculate total price
                cursor.execute("SELECT PRICE FROM CPU WHERE CPU_ID = %s", (cpu_id,))
                cpu_price = cursor.fetchone()[0]

                cursor.execute("SELECT PRICE FROM GPU WHERE GPU_ID = %s", (gpu_id,))
                gpu_price = cursor.fetchone()[0]

                cursor.execute("SELECT PRICE FROM RAM WHERE RAM_ID = %s", (ram_id,))
                ram_price = cursor.fetchone()[0]

                cursor.execute("SELECT PRICE FROM POWER_SUPPLY WHERE PSU_ID = %s", (psu_id,))
                psu_price = cursor.fetchone()[0]

                cursor.execute("SELECT PRICE FROM MONITOR WHERE MON_ID = %s", (mon_id,))
                mon_price = cursor.fetchone()[0]

                cursor.execute("SELECT PRICE FROM MOTHERBOARD WHERE MB_ID = %s", (mb_id,))
                mb_price = cursor.fetchone()[0]

                cursor.execute("SELECT PRICE FROM STORAGE WHERE STR_ID = %s", (str_id,))
                str_price = cursor.fetchone()[0]

                # Calculate total price
                total_price = cpu_price + gpu_price + ram_price + psu_price + mon_price + mb_price + str_price

                # Insert new build into the PC_BUILD table
                cursor.execute("INSERT INTO PC_BUILD (CPU_ID, GPU_ID, RAM_ID, PSU_ID, MON_ID, MB_ID, STR_ID, TOTAL_PRICE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
                               (cpu_id, gpu_id, ram_id, psu_id, mon_id, mb_id, str_id, total_price))
                connection.commit()

                # Get the BUILD_ID of the newly added build
                cursor.execute("SELECT LAST_INSERT_ID()")
                build_id = cursor.fetchone()[0]

                # Insert into USER_BUILDS to associate the build with the user
                username = st.session_state.get('username')
                if username:
                    cursor.execute("INSERT INTO USER_BUILDS (USERNAME, BUILD_ID) VALUES (%s, %s)", (username, build_id))
                    connection.commit()

                st.success("Build added successfully!")
        except Error as e:
            st.error(f"Error occurred while adding build: {e}")
        finally:
            cursor.close()
            close_connection(connection)

def view_my_builds():
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            username = st.session_state.get('username')
            if username:
                query = """
                SELECT pc.BUILD_ID, cpu.BRAND AS CPU_BRAND, cpu.MODEL AS CPU_MODEL, gpu.BRAND AS GPU_BRAND, gpu.MODEL AS GPU_MODEL,
                       ram.BRAND AS RAM_BRAND, ram.CAPACITY AS RAM_CAPACITY, ps.BRAND AS PSU_BRAND, ps.WATTAGE AS PSU_WATTAGE,
                       mon.BRAND AS MONITOR_BRAND, mon.SIZE AS MONITOR_SIZE, mb.BRAND AS MB_BRAND, strg.BRAND AS STORAGE_BRAND,
                       strg.TYPE AS STORAGE_TYPE, strg.CAPACITY AS STORAGE_CAPACITY, pc.TOTAL_PRICE
                FROM PC_BUILD pc
                JOIN CPU cpu ON pc.CPU_ID = cpu.CPU_ID
                JOIN GPU gpu ON pc.GPU_ID = gpu.GPU_ID
                JOIN RAM ram ON pc.RAM_ID = ram.RAM_ID
                JOIN POWER_SUPPLY ps ON pc.PSU_ID = ps.PSU_ID
                JOIN MONITOR mon ON pc.MON_ID = mon.MON_ID
                JOIN MOTHERBOARD mb ON pc.MB_ID = mb.MB_ID
                JOIN STORAGE strg ON pc.STR_ID = strg.STR_ID
                WHERE pc.BUILD_ID IN (SELECT BUILD_ID FROM USER_BUILDS WHERE USERNAME = %s)
                """
                df = pd.read_sql(query, connection, params=(username,))
                st.dataframe(df)
        except Error as e:
            st.error(f"Error occurred: {e}")
        finally:
            close_connection(connection)

def main():
    st.title("PC Build Management System")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        choice = st.sidebar.selectbox("Login/Register", ["Login", "Register"])
        if choice == "Login":
            st.sidebar.subheader("Login")
            username = st.sidebar.text_input("Username")
            password = st.sidebar.text_input("Password", type="password")
            if st.sidebar.button("Login"):
                if login_user(username, password):
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.success(f"Welcome {username}!")
                    welcome_page()
                else:
                    st.error("Invalid username or password")
        elif choice == "Register":
            st.sidebar.subheader("Register")
            username = st.sidebar.text_input("New Username")
            password = st.sidebar.text_input("New Password", type="password")
            if st.sidebar.button("Register"):
                if username and password:
                    register_user(username, password)
                else:
                    st.error("Username and password cannot be blank")
    else:
        welcome_page()

def welcome_page():
    st.sidebar.title("Navigation")
    action = st.sidebar.selectbox("Choose Action", ["View Existing Builds", "Add a New Build", "View My Builds", "View Component Tables"])

    if action == "View Existing Builds":
        st.header("Existing Builds")
        view_existing_builds()

    elif action == "Add a New Build":
        st.header("Add a New Build")
        add_new_build()

    elif action == "View My Builds":
        st.header("My Builds")
        view_my_builds()

    elif action == "View Component Tables":
        component = st.selectbox("Select Component Table to View", ["CPU", "GPU", "RAM", "POWER_SUPPLY", "MOTHERBOARD", "STORAGE", "MONITOR"])
        connection = create_connection()
        query = f"SELECT * FROM {component}"
        df = pd.read_sql(query, connection)
        connection.close()
        st.dataframe(df)

if __name__ == "__main__":
    main()
