import streamlit as st
import pandas as pd
from sqlalchemy import text

# Create a SQL connection
conn = st.connection(
    "mundo_db",
    type="sql",
    dialect="mysql",
    host="localhost",
    database="mundo",
    username="root",  # Add your MySQL  username
    password="Zyzser-resbih-kezqu0"   # Using Streamlit secrets for MySQL password
)

def main():
    st.title("CRUD bases de datos")

    st.sidebar.markdown("**Esta es una aplicacion para realizar CRUD con las bases de datos del root**")
    
    # Display Options for tables
    table = st.sidebar.selectbox(
        "Select a Table", 
        ("City", "Country", "CountryLanguage")
    )
    
    # Display Options for CRUD Operations
    operation = st.sidebar.selectbox(
        "Select an Operation", 
        ("Create", "Read", "Update", "Delete")
    ) 
    
    # CITY TABLE OPERATIONS
    if table == "City":
        if operation == "Create":
            st.subheader("Add New City")
            
            # Get country codes for dropdown
            countries = conn.query("SELECT Code, Name FROM country ORDER BY Name")
            country_options = {f"{country['Name']} ({country['Code']})": country['Code'] for country in countries.to_dict('records')}
            
            with st.form("create_city_form"):
                name = st.text_input("City Name")
                country_selection = st.selectbox(
                    "Country", 
                    options=list(country_options.keys())
                )
                country_code = country_options[country_selection]
                district = st.text_input("District")
                population = st.number_input("Population", min_value=0, step=1000)
                
                submit_button = st.form_submit_button("Add City")
                
                if submit_button:
                    if name and district:
                        try:
                            with conn.session as session:
                                session.execute(
                                    text("INSERT INTO city(Name, CountryCode, District, Population) VALUES(:name, :country_code, :district, :population)"),
                                    {"name": name, "country_code": country_code, "district": district, "population": population}
                                )
                                session.commit()
                            st.success("City Added Successfully!")
                            # Reset the cache for this table
                            conn.reset()
                        except Exception as e:
                            st.error(f"Error adding city: {e}")
                    else:
                        st.warning("Please fill in all required fields")
        
        elif operation == "Read":
            st.subheader("City Information")
            
            # Search options
            search_option = st.radio(
                "Search by:",
                ["All Cities", "Country", "Population Range", "District"]
            )
            
            try:
                if search_option == "All Cities":
                    # Add pagination for large datasets
                    page_size = st.slider("Cities per page", 10, 100, 25)
                    page = st.number_input("Page", min_value=1, value=1)
                    offset = (page - 1) * page_size
                    
                    cities = conn.query(
                        f"""
                        SELECT city.ID, city.Name, country.Name as Country, 
                        city.District, city.Population 
                        FROM city 
                        JOIN country ON city.CountryCode = country.Code
                        ORDER BY city.Population DESC
                        LIMIT {page_size} OFFSET {offset}
                        """
                    )
                    
                elif search_option == "Country":
                    countries = conn.query("SELECT Code, Name FROM country ORDER BY Name")
                    country_options = {country['Name']: country['Code'] for country in countries.to_dict('records')}
                    selected_country = st.selectbox("Select Country", list(country_options.keys()))
                    country_code = country_options[selected_country]
                    
                    cities = conn.query(
                        """
                        SELECT city.ID, city.Name, country.Name as Country, 
                        city.District, city.Population 
                        FROM city 
                        JOIN country ON city.CountryCode = country.Code
                        WHERE city.CountryCode = :country_code
                        ORDER BY city.Population DESC
                        """,
                        params={"country_code": country_code}
                    )
                
                elif search_option == "Population Range":
                    min_pop = st.number_input("Minimum Population", min_value=0, value=100000, step=10000)
                    max_pop = st.number_input("Maximum Population", min_value=0, value=5000000, step=10000)
                    
                    cities = conn.query(
                        """
                        SELECT city.ID, city.Name, country.Name as Country, 
                        city.District, city.Population 
                        FROM city 
                        JOIN country ON city.CountryCode = country.Code
                        WHERE city.Population BETWEEN :min_pop AND :max_pop
                        ORDER BY city.Population DESC
                        """,
                        params={"min_pop": min_pop, "max_pop": max_pop}
                    )
                
                elif search_option == "District":
                    district_input = st.text_input("Enter District")
                    if district_input:
                        cities = conn.query(
                            """
                            SELECT city.ID, city.Name, country.Name as Country, 
                            city.District, city.Population 
                            FROM city 
                            JOIN country ON city.CountryCode = country.Code
                            WHERE city.District LIKE :district
                            ORDER BY city.Population DESC
                            """,
                            params={"district": f"%{district_input}%"}
                        )
                    else:
                        st.warning("Please enter a district name")
                        return
                
                if not cities.empty:
                    st.dataframe(cities)
                    st.write(f"Found {len(cities)} cities")
                else:
                    st.info("No cities found matching your criteria")
                    
            except Exception as e:
                st.error(f"Error retrieving city data: {e}")
        
        elif operation == "Update":
            st.subheader("Update City Information")
            
            # Search for city to update
            search_term = st.text_input("Search for a city by name")
            
            if search_term:
                try:
                    cities = conn.query(
                        """
                        SELECT city.ID, city.Name, country.Name as Country, 
                        city.CountryCode, city.District, city.Population 
                        FROM city 
                        JOIN country ON city.CountryCode = country.Code
                        WHERE city.Name LIKE :search_term
                        LIMIT 100
                        """,
                        params={"search_term": f"%{search_term}%"}
                    )
                    
                    if cities.empty:
                        st.info("No cities found with that name")
                        return
                    
                    city_options = {f"{row['Name']}, {row['Country']} (ID: {row['ID']})": row['ID'] for _, row in cities.iterrows()}
                    selected_city = st.selectbox(
                        "Select city to update", 
                        options=list(city_options.keys())
                    )
                    city_id = city_options[selected_city]
                    
                    # Get current city data
                    city_data = conn.query(
                        "SELECT * FROM city WHERE ID = :city_id",
                        params={"city_id": city_id}
                    ).iloc[0]
                    
                    # Get country list for dropdown
                    countries = conn.query("SELECT Code, Name FROM country ORDER BY Name")
                    country_options = {f"{row['Name']} ({row['Code']})": row['Code'] for _, row in countries.iterrows()}
                    
                    # Find current country in options
                    current_country_code = city_data['CountryCode']
                    current_country_name = conn.query(
                        "SELECT Name FROM country WHERE Code = :code",
                        params={"code": current_country_code}
                    ).iloc[0]['Name']
                    current_country = f"{current_country_name} ({current_country_code})"
                    
                    with st.form("update_city_form"):
                        name = st.text_input("City Name", value=city_data['Name'])
                        country_selection = st.selectbox(
                            "Country", 
                            options=list(country_options.keys()),
                            index=list(country_options.keys()).index(current_country) if current_country in country_options else 0
                        )
                        country_code = country_options[country_selection]
                        district = st.text_input("District", value=city_data['District'])
                        population = st.number_input("Population", value=city_data['Population'], min_value=0, step=1000)
                        
                        submit_button = st.form_submit_button("Update City")
                        
                        if submit_button:
                            if name and district:
                                try:
                                    with conn.session as session:
                                        session.execute(
                                            text("UPDATE city SET Name=:name, CountryCode=:country_code, District=:district, Population=:population WHERE ID=:city_id"),
                                            {"name": name, "country_code": country_code, "district": district, "population": population, "city_id": city_id}
                                        )
                                        session.commit()
                                    st.success("City Updated Successfully!")
                                    # Reset the cache for this table
                                    conn.reset()
                                except Exception as e:
                                    st.error(f"Error updating city: {e}")
                            else:
                                st.warning("Please fill in all required fields")
                
                except Exception as e:
                    st.error(f"Error: {e}")
        
        elif operation == "Delete":
            st.subheader("Delete City")
            
            # Search for city to delete
            search_term = st.text_input("Search for a city by name")
            
            if search_term:
                try:
                    cities = conn.query(
                        """
                        SELECT city.ID, city.Name, country.Name as Country, 
                        city.District, city.Population 
                        FROM city 
                        JOIN country ON city.CountryCode = country.Code
                        WHERE city.Name LIKE :search_term
                        LIMIT 100
                        """,
                        params={"search_term": f"%{search_term}%"}
                    )
                    
                    if cities.empty:
                        st.info("No cities found with that name")
                        return
                    
                    city_options = {f"{row['Name']}, {row['Country']} (ID: {row['ID']})": row['ID'] for _, row in cities.iterrows()}
                    selected_city = st.selectbox(
                        "Select city to delete", 
                        options=list(city_options.keys())
                    )
                    city_id = city_options[selected_city]
                    
                    st.warning(f"Are you sure you want to delete {selected_city}?")
                    confirm = st.checkbox("I confirm I want to delete this city")
                    
                    if st.button("Delete City") and confirm:
                        try:
                            with conn.session as session:
                                session.execute(
                                    text("DELETE FROM city WHERE ID=:city_id"),
                                    {"city_id": city_id}
                                )
                                session.commit()
                            st.success("City Deleted Successfully!")
                            # Reset the cache for this table
                            conn.reset()
                        except Exception as e:
                            st.error(f"Error deleting city: {e}")
                
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # COUNTRY TABLE OPERATIONS
    elif table == "Country":
        if operation == "Create":
            st.subheader("Add New Country")
            
            with st.form("create_country_form"):
                code = st.text_input("Country Code (3 characters)", max_chars=3)
                name = st.text_input("Country Name")
                continent = st.selectbox(
                    "Continent", 
                    ["Asia", "Europe", "North America", "Africa", "Oceania", "Antarctica", "South America"]
                )
                region = st.text_input("Region")
                surface_area = st.number_input("Surface Area (sq km)", min_value=0.0, step=1.0)
                indep_year = st.number_input("Independence Year", min_value=0, step=1)
                population = st.number_input("Population", min_value=0, step=1000)
                life_expectancy = st.number_input("Life Expectancy", min_value=0.0, max_value=100.0, step=0.1)
                gnp = st.number_input("GNP (USD)", min_value=0.0, step=1.0)
                gnp_old = st.number_input("Old GNP (USD)", min_value=0.0, step=1.0)
                local_name = st.text_input("Local Name")
                government_form = st.text_input("Government Form")
                head_of_state = st.text_input("Head of State")
                
                # For capital, we need to get cities first
                cities = conn.query("SELECT ID, Name FROM city ORDER BY Name")
                city_options = {row['Name']: row['ID'] for _, row in cities.iterrows()}
                city_options["None"] = None
                capital_selection = st.selectbox("Capital City", options=list(city_options.keys()))
                capital = city_options[capital_selection]
                
                code2 = st.text_input("Country Code 2 (2 characters)", max_chars=2)
                
                submit_button = st.form_submit_button("Add Country")
                
                if submit_button:
                    if code and name and continent and region:
                        try:
                            with conn.session as session:
                                session.execute(
                                    text("""
                                        INSERT INTO country(
                                            Code, Name, Continent, Region, SurfaceArea, 
                                            IndepYear, Population, LifeExpectancy, GNP, 
                                            GNPOld, LocalName, GovernmentForm, HeadOfState, 
                                            Capital, Code2
                                        ) VALUES(
                                            :code, :name, :continent, :region, :surface_area, 
                                            :indep_year, :population, :life_expectancy, :gnp, 
                                            :gnp_old, :local_name, :government_form, :head_of_state, 
                                            :capital, :code2
                                        )
                                    """),
                                    {
                                        "code": code, 
                                        "name": name, 
                                        "continent": continent, 
                                        "region": region, 
                                        "surface_area": surface_area, 
                                        "indep_year": indep_year if indep_year > 0 else None, 
                                        "population": population, 
                                        "life_expectancy": life_expectancy if life_expectancy > 0 else None, 
                                        "gnp": gnp, 
                                        "gnp_old": gnp_old, 
                                        "local_name": local_name, 
                                        "government_form": government_form, 
                                        "head_of_state": head_of_state if head_of_state else None, 
                                        "capital": capital, 
                                        "code2": code2
                                    }
                                )
                                session.commit()
                            st.success("Country Added Successfully!")
                            # Reset the cache for this table
                            conn.reset()
                        except Exception as e:
                            st.error(f"Error adding country: {e}")
                    else:
                        st.warning("Please fill in all required fields")
        
        elif operation == "Read":
            st.subheader("Country Information")
            
            # Search options
            search_option = st.radio(
                "Search by:",
                ["All Countries", "Continent", "Region", "Population Range"]
            )
            
            try:
                if search_option == "All Countries":
                    countries = conn.query(
                        """
                        SELECT c.Code, c.Name, c.Continent, c.Region, 
                        c.SurfaceArea, c.IndepYear, c.Population, 
                        c.LifeExpectancy, c.GNP, c.LocalName, 
                        c.GovernmentForm, c.HeadOfState, city.Name as Capital
                        FROM country c
                        LEFT JOIN city ON c.Capital = city.ID
                        ORDER BY c.Name
                        """
                    )
                
                elif search_option == "Continent":
                    continent = st.selectbox(
                        "Select Continent", 
                        ["Asia", "Europe", "North America", "Africa", "Oceania", "Antarctica", "South America"]
                    )
                    
                    countries = conn.query(
                        """
                        SELECT c.Code, c.Name, c.Continent, c.Region, 
                        c.SurfaceArea, c.IndepYear, c.Population, 
                        c.LifeExpectancy, c.GNP, c.LocalName, 
                        c.GovernmentForm, c.HeadOfState, city.Name as Capital
                        FROM country c
                        LEFT JOIN city ON c.Capital = city.ID
                        WHERE c.Continent = :continent
                        ORDER BY c.Name
                        """,
                        params={"continent": continent}
                    )
                
                elif search_option == "Region":
                    # Get unique regions
                    regions = conn.query("SELECT DISTINCT Region FROM country ORDER BY Region")
                    region = st.selectbox("Select Region", regions['Region'].tolist())
                    
                    countries = conn.query(
                        """
                        SELECT c.Code, c.Name, c.Continent, c.Region, 
                        c.SurfaceArea, c.IndepYear, c.Population, 
                        c.LifeExpectancy, c.GNP, c.LocalName, 
                        c.GovernmentForm, c.HeadOfState, city.Name as Capital
                        FROM country c
                        LEFT JOIN city ON c.Capital = city.ID
                        WHERE c.Region = :region
                        ORDER BY c.Name
                        """,
                        params={"region": region}
                    )
                
                elif search_option == "Population Range":
                    min_pop = st.number_input("Minimum Population", min_value=0, value=1000000, step=1000000)
                    max_pop = st.number_input("Maximum Population", min_value=0, value=100000000, step=1000000)
                    
                    countries = conn.query(
                        """
                        SELECT c.Code, c.Name, c.Continent, c.Region, 
                        c.SurfaceArea, c.IndepYear, c.Population, 
                        c.LifeExpectancy, c.GNP, c.LocalName, 
                        c.GovernmentForm, c.HeadOfState, city.Name as Capital
                        FROM country c
                        LEFT JOIN city ON c.Capital = city.ID
                        WHERE c.Population BETWEEN :min_pop AND :max_pop
                        ORDER BY c.Population DESC
                        """,
                        params={"min_pop": min_pop, "max_pop": max_pop}
                    )
                
                if not countries.empty:
                    st.dataframe(countries)
                    st.write(f"Found {len(countries)} countries")
                else:
                    st.info("No countries found matching your criteria")
                    
            except Exception as e:
                st.error(f"Error retrieving country data: {e}")
        
        elif operation == "Update":
            st.subheader("Update Country Information")
            
            # Get country list
            try:
                countries = conn.query("SELECT Code, Name FROM country ORDER BY Name")
                country_options = {row['Name']: row['Code'] for _, row in countries.iterrows()}
                selected_country_name = st.selectbox("Select Country to Update", list(country_options.keys()))
                country_code = country_options[selected_country_name]
                
                # Get current country data
                country_data = conn.query(
                    "SELECT * FROM country WHERE Code = :code",
                    params={"code": country_code}
                ).iloc[0]
                
                with st.form("update_country_form"):
                    name = st.text_input("Country Name", value=country_data['Name'])
                    continent = st.selectbox(
                        "Continent", 
                        ["Asia", "Europe", "North America", "Africa", "Oceania", "Antarctica", "South America"],
                        index=["Asia", "Europe", "North America", "Africa", "Oceania", "Antarctica", "South America"].index(country_data['Continent'])
                    )
                    region = st.text_input("Region", value=country_data['Region'])
                    surface_area = st.number_input("Surface Area (sq km)", value=float(country_data['SurfaceArea']), min_value=0.0, step=1.0)
                    indep_year = st.number_input("Independence Year", value=country_data['IndepYear'] if country_data['IndepYear'] else 0, min_value=0, step=1)
                    population = st.number_input("Population", value=country_data['Population'], min_value=0, step=1000)
                    life_expectancy = st.number_input("Life Expectancy", value=float(country_data['LifeExpectancy']) if country_data['LifeExpectancy'] else 0.0, min_value=0.0, max_value=100.0, step=0.1)
                    gnp = st.number_input("GNP (USD)", value=float(country_data['GNP']) if country_data['GNP'] else 0.0, min_value=0.0, step=1.0)
                    gnp_old = st.number_input("Old GNP (USD)", value=float(country_data['GNPOld']) if country_data['GNPOld'] else 0.0, min_value=0.0, step=1.0)
                    local_name = st.text_input("Local Name", value=country_data['LocalName'])
                    government_form = st.text_input("Government Form", value=country_data['GovernmentForm'])
                    head_of_state = st.text_input("Head of State", value=country_data['HeadOfState'] if country_data['HeadOfState'] else "")
                    
                    # For capital, we need to get cities first
                    cities = conn.query("SELECT ID, Name FROM city WHERE CountryCode = :code ORDER BY Name", params={"code": country_code})
                    city_options = {row['Name']: row['ID'] for _, row in cities.iterrows()}
                    city_options["None"] = None
                    
                    # Find current capital
                    current_capital_id = country_data['Capital']
                    if current_capital_id:
                        current_capital = conn.query(
                            "SELECT Name FROM city WHERE ID = :id",
                            params={"id": current_capital_id}
                        )
                        current_capital_name = current_capital.iloc[0]['Name'] if not current_capital.empty else "None"
                    else:
                        current_capital_name = "None"
                    
                    capital_selection = st.selectbox(
                        "Capital City", 
                        options=list(city_options.keys()),
                        index=list(city_options.keys()).index(current_capital_name) if current_capital_name in city_options else 0
                    )
                    capital = city_options[capital_selection]
                    
                    code2 = st.text_input("Country Code 2 (2 characters)", value=country_data['Code2'], max_chars=2)
                    
                    submit_button = st.form_submit_button("Update Country")
                    
                    if submit_button:
                        if name and continent and region:
                            try:
                                with conn.session as session:
                                    session.execute(
                                        text("""
                                            UPDATE country SET 
                                            Name=:name, Continent=:continent, Region=:region, SurfaceArea=:surface_area, 
                                            IndepYear=:indep_year, Population=:population, LifeExpectancy=:life_expectancy, GNP=:gnp, 
                                            GNPOld=:gnp_old, LocalName=:local_name, GovernmentForm=:government_form, HeadOfState=:head_of_state, 
                                            Capital=:capital, Code2=:code2
                                            WHERE Code=:code
                                        """),
                                        {
                                            "name": name, 
                                            "continent": continent, 
                                            "region": region, 
                                            "surface_area": surface_area, 
                                            "indep_year": indep_year if indep_year > 0 else None, 
                                            "population": population, 
                                            "life_expectancy": life_expectancy if life_expectancy > 0 else None, 
                                            "gnp": gnp, 
                                            "gnp_old": gnp_old, 
                                            "local_name": local_name, 
                                            "government_form": government_form, 
                                            "head_of_state": head_of_state if head_of_state else None, 
                                            "capital": capital, 
                                            "code2": code2, 
                                            "code": country_code
                                        }
                                    )
                                    session.commit()
                                st.success("Country Updated Successfully!")
                                # Reset the cache for this table
                                conn.reset()
                            except Exception as e:
                                st.error(f"Error updating country: {e}")
                        else:
                            st.warning("Please fill in all required fields")
            
            except Exception as e:
                st.error(f"Error: {e}")
        
        elif operation == "Delete":
            st.subheader("Delete Country")
            st.warning("⚠️ Deleting a country will also delete all associated cities and language records due to database constraints!")
            
            # Get country list
            try:
                countries = conn.query("SELECT Code, Name FROM country ORDER BY Name")
                country_options = {row['Name']: row['Code'] for _, row in countries.iterrows()}
                selected_country = st.selectbox("Select Country to Delete", list(country_options.keys()))
                country_code = country_options[selected_country]
                
                # Show country details before deletion
                country_info = conn.query(
                    """
                    SELECT c.Name, c.Continent, c.Region, c.Population,
                    (SELECT COUNT(*) FROM city WHERE CountryCode = c.Code) as CityCount,
                    (SELECT COUNT(*) FROM countrylanguage WHERE CountryCode = c.Code) as LanguageCount
                    FROM country c
                    WHERE c.Code = :code
                    """,
                    params={"code": country_code}
                ).iloc[0]
                
                st.write(f"Country: {country_info['Name']}")
                st.write(f"Continent: {country_info['Continent']}")
                st.write(f"Region: {country_info['Region']}")
                st.write(f"Population: {country_info['Population']:,}")
                st.write(f"Number of cities in database: {country_info['CityCount']}")
                st.write(f"Number of languages in database: {country_info['LanguageCount']}")
                
                st.warning(f"Are you sure you want to delete {selected_country} and all its related data?")
                confirm = st.checkbox("I confirm I want to delete this country and understand this will delete related cities and language records")
                
                if st.button("Delete Country") and confirm:
                    try:
                        with conn.session as session:
                            # Start a transaction (already handled by session context)
                            
                            # Delete language records first
                            session.execute(
                                text("DELETE FROM countrylanguage WHERE CountryCode = :code"),
                                {"code": country_code}
                            )
                            
                            # Delete cities
                            session.execute(
                                text("DELETE FROM city WHERE CountryCode = :code"),
                                {"code": country_code}
                            )
                            
                            # Delete country
                            session.execute(
                                text("DELETE FROM country WHERE Code = :code"),
                                {"code": country_code}
                            )
                            
                            # Commit the transaction
                            session.commit()
                        st.success("Country and related data deleted successfully!")
                        # Reset the cache for this table
                        conn.reset()
                    except Exception as e:
                        st.error(f"Error deleting country: {e}")
            
            except Exception as e:
                st.error(f"Error: {e}")
    
    # COUNTRYLANGUAGE TABLE OPERATIONS
    elif table == "CountryLanguage":
        if operation == "Create":
            st.subheader("Add New Language")
            
            # Get country list
            try:
                countries = conn.query("SELECT Code, Name FROM country ORDER BY Name")
                country_options = {row['Name']: row['Code'] for _, row in countries.iterrows()}
                selected_country = st.selectbox("Select Country", list(country_options.keys()))
                country_code = country_options[selected_country]
                
                with st.form("create_language_form"):
                    language = st.text_input("Language")
                    is_official = st.selectbox("Is Official", ["T", "F"])
                    percentage = st.slider("Percentage of Population", min_value=0.0, max_value=100.0, step=0.1)
                    
                    submit_button = st.form_submit_button("Add Language")
                    
                    if submit_button:
                        if language:
                            try:
                                with conn.session as session:
                                    session.execute(
                                        text("INSERT INTO countrylanguage(CountryCode, Language, IsOfficial, Percentage) VALUES(:country_code, :language, :is_official, :percentage)"),
                                        {"country_code": country_code, "language": language, "is_official": is_official, "percentage": percentage}
                                    )
                                    session.commit()
                                st.success("Language Added Successfully!")
                                # Reset the cache for this table
                                conn.reset()
                            except Exception as e:
                                st.error(f"Error adding language: {e}")
                        else:
                            st.warning("Please enter a language name")
            
            except Exception as e:
                st.error(f"Error: {e}")
        
        elif operation == "Read":
            st.subheader("Language Information")
            
            # Search options
            search_option = st.radio(
                "Search by:",
                ["All Languages", "Country", "Language Name", "Official Languages"]
            )
            
            try:
                if search_option == "All Languages":
                    languages = conn.query(
                        """
                        SELECT cl.Language, c.Name as Country, 
                        CASE WHEN cl.IsOfficial = 'T' THEN 'Yes' ELSE 'No' END as Official,
                        cl.Percentage
                        FROM countrylanguage cl
                        JOIN country c ON cl.CountryCode = c.Code
                        ORDER BY cl.Language, c.Name
                        """
                    )
                
                elif search_option == "Country":
                    countries = conn.query("SELECT Code, Name FROM country ORDER BY Name")
                    country_options = {row['Name']: row['Code'] for _, row in countries.iterrows()}
                    selected_country = st.selectbox("Select Country", list(country_options.keys()))
                    country_code = country_options[selected_country]
                    
                    languages = conn.query(
                        """
                        SELECT cl.Language, 
                        CASE WHEN cl.IsOfficial = 'T' THEN 'Yes' ELSE 'No' END as Official,
                        cl.Percentage
                        FROM countrylanguage cl
                        WHERE cl.CountryCode = :country_code
                        ORDER BY cl.Percentage DESC
                        """,
                        params={"country_code": country_code}
                    )
                
                elif search_option == "Language Name":
                    language_name = st.text_input("Enter Language Name")
                    if language_name:
                        languages = conn.query(
                            """
                            SELECT cl.Language, c.Name as Country, 
                            CASE WHEN cl.IsOfficial = 'T' THEN 'Yes' ELSE 'No' END as Official,
                            cl.Percentage
                            FROM countrylanguage cl
                            JOIN country c ON cl.CountryCode = c.Code
                            WHERE cl.Language LIKE :language_name
                            ORDER BY cl.Percentage DESC
                            """,
                            params={"language_name": f"%{language_name}%"}
                        )
                    else:
                        st.warning("Please enter a language name")
                        return
                
                elif search_option == "Official Languages":
                    languages = conn.query(
                        """
                        SELECT cl.Language, c.Name as Country, cl.Percentage
                        FROM countrylanguage cl
                        JOIN country c ON cl.CountryCode = c.Code
                        WHERE cl.IsOfficial = 'T'
                        ORDER BY cl.Language, c.Name
                        """
                    )
                
                if not languages.empty:
                    st.dataframe(languages)
                    st.write(f"Found {len(languages)} language records")
                else:
                    st.info("No languages found matching your criteria")
                    
            except Exception as e:
                st.error(f"Error retrieving language data: {e}")
        
        elif operation == "Update":
            st.subheader("Update Language Information")
            
            # Get country list
            try:
                countries = conn.query("SELECT Code, Name FROM country ORDER BY Name")
                country_options = {row['Name']: row['Code'] for _, row in countries.iterrows()}
                selected_country = st.selectbox("Select Country", list(country_options.keys()))
                country_code = country_options[selected_country]
                
                # Get languages for this country
                languages = conn.query(
                    """
                    SELECT Language, IsOfficial, Percentage 
                    FROM countrylanguage 
                    WHERE CountryCode = :country_code
                    ORDER BY Percentage DESC
                    """,
                    params={"country_code": country_code}
                )
                
                if languages.empty:
                    st.info(f"No languages found for {selected_country}")
                    return
                
                language_options = {row['Language']: row['Language'] for _, row in languages.iterrows()}
                selected_language = st.selectbox("Select Language to Update", list(language_options.keys()))
                
                # Get current language data
                language_data = conn.query(
                    """
                    SELECT IsOfficial, Percentage 
                    FROM countrylanguage 
                    WHERE CountryCode = :country_code AND Language = :language
                    """,
                    params={"country_code": country_code, "language": selected_language}
                ).iloc[0]
                
                with st.form("update_language_form"):
                    is_official = st.selectbox(
                        "Is Official", 
                        ["T", "F"],
                        index=0 if language_data['IsOfficial'] == 'T' else 1
                    )
                    percentage = st.slider(
                        "Percentage of Population", 
                        min_value=0.0, 
                        max_value=100.0, 
                        value=float(language_data['Percentage']),
                        step=0.1
                    )
                    
                    submit_button = st.form_submit_button("Update Language")
                    
                    if submit_button:
                        try:
                            with conn.session as session:
                                session.execute(
                                    text("UPDATE countrylanguage SET IsOfficial=:is_official, Percentage=:percentage WHERE CountryCode=:country_code AND Language=:language"),
                                    {"is_official": is_official, "percentage": percentage, "country_code": country_code, "language": selected_language}
                                )
                                session.commit()
                            st.success("Language Updated Successfully!")
                            # Reset the cache for this table
                            conn.reset()
                        except Exception as e:
                            st.error(f"Error updating language: {e}")
            
            except Exception as e:
                st.error(f"Error: {e}")
        
        elif operation == "Delete":
            st.subheader("Delete Language")
            
            # Get country list
            try:
                countries = conn.query("SELECT Code, Name FROM country ORDER BY Name")
                country_options = {row['Name']: row['Code'] for _, row in countries.iterrows()}
                selected_country = st.selectbox("Select Country", list(country_options.keys()))
                country_code = country_options[selected_country]
                
                # Get languages for this country
                languages = conn.query(
                    """
                    SELECT Language, IsOfficial, Percentage 
                    FROM countrylanguage 
                    WHERE CountryCode = :country_code
                    ORDER BY Percentage DESC
                    """,
                    params={"country_code": country_code}
                )
                
                if languages.empty:
                    st.info(f"No languages found for {selected_country}")
                    return
                
                language_options = {row['Language']: row['Language'] for _, row in languages.iterrows()}
                selected_language = st.selectbox("Select Language to Delete", list(language_options.keys()))
                
                # Show language details
                language_data = conn.query(
                    """
                    SELECT IsOfficial, Percentage 
                    FROM countrylanguage 
                    WHERE CountryCode = :country_code AND Language = :language
                    """,
                    params={"country_code": country_code, "language": selected_language}
                ).iloc[0]
                
                st.write(f"Language: {selected_language}")
                st.write(f"Country: {selected_country}")
                st.write(f"Official: {'Yes' if language_data['IsOfficial'] == 'T' else 'No'}")
                st.write(f"Percentage: {language_data['Percentage']}%")
                
                st.warning(f"Are you sure you want to delete {selected_language} for {selected_country}?")
                confirm = st.checkbox("I confirm I want to delete this language record")
                
                if st.button("Delete Language") and confirm:
                    try:
                        with conn.session as session:
                            session.execute(
                                text("DELETE FROM countrylanguage WHERE CountryCode=:country_code AND Language=:language"),
                                {"country_code": country_code, "language": selected_language}
                            )
                            session.commit()
                        st.success("Language Deleted Successfully!")
                        # Reset the cache for this table
                        conn.reset()
                    except Exception as e:
                        st.error(f"Error deleting language: {e}")
            
            except Exception as e:
                st.error(f"Error: {e}")

if __name__ == "__main__":
    main()
