#define the structure of a column
class Column:
    def __init__(self, name, data_type):
        self.name = name
        self.dataType = data_type

    def __repr__(self):
        return f'{self.name} ({self.dataType.__name__})'

#define the table structure
class Table:
    def __init__(self, name ):
        self.name = name
        self.columns = []
        self.rows = []

    def add_column(self, column):
        self.columns.append(column)

    def add_row(self, row):
        self.rows.append(row)

    def __repr__(self):
        columns_str = ", ".join([str(c) for c in self.columns])
        return f"Tabella '{self.name}' [ Colonne: {columns_str} | Righe inserite: {len(self.rows)} ]"


class Database:
    def __init__(self, name):
        self.name = name
        self.tables = {}
    def get_table(self, table_name):
        return self.tables.get(table_name, [])

    def add_table(self, table):
        self.tables[table.name] = table

    def __repr__(self):
        tables_name = list(self.tables.keys())
        return f"Database '{self.name}' [ Tabelle presenti: {tables_name} ]"

# -------------- FUCNTION TO SET UP YOUR OWN DB ---------------------------- #

#create columns of a tables
def create_new_table(db):
    print("\n--- CREAZIONE NUOVA TABELLA ---")
    table_name = input("Inserisci il nome della tabella che vuoi creare: ").strip()

    if not table_name:
        return "Non puoi creare una tabella senza nome"

    if db.get_table(table_name):
        return f"Tabella '{table_name}' esiste già"

    new_table = Table(table_name)

    print("Aggiungi le colonne (premi invio senza scrivere nulla per terminare):")
    while True:
        column_name = input("Nome colonna: ").strip()
        if not column_name:
            break

        type_column = input("  Tipo di dato ('str' per testo, 'int' per numero): ").strip().lower()
        data_type = int if type_column == "int" else str

        new_table.add_column(Column(column_name, data_type))
        print(f"  -> Colonna '{column_name}' ({data_type.__name__}) aggiunta.")

        if len(new_table.columns) == 0:
            print("Non puoi creare una tabella priva di colonne")
            return

    db.add_table(new_table)
    print(f"\nColonna creata con successo!")

#insert data in your created table
def insert_data(db):
    print("\n--- INSERISCI DATI NELLA TABELLA ---")
    table_name = input("Inserisci il nome della tabella che vuoi creare: ").strip()

    table = db.get_table(table_name)
    if not table:
        return "La tabella richiesta non esiste"

    print(f"Inserimento dati per la tabella '{table_name}':")
    new_row = {}

    for col in table.columns:
        col_input = input(f"  Inserisci valore per '{col.name}' ({col.dataType.__name__}): ").strip()

        #check if the data type provide are corrects
        if col.dataType == int:
            try:
                col_input = int(col_input)
            except ValueError:
                print("f Attenzione: Valore non valido per intero. Salvato come 0.")
                col_input = 0


        new_row[col.name] = col_input

    table.add_row(new_row)
    print(f"\nRiga inserita con successo!")


#------- FUNCTION FOR SQL PARSER -------- #

def apply_projection(rows, columns_requested):
    if columns_requested == "*":
        return rows

    columns_list = [col.strip() for col in columns_requested.split(',')]
    final_rows = []
    for row in rows:
        filtered_row = {}
        for col in columns_list:
            if col in row:
                filtered_row[col] = row[col]
            else:
                return f"Non esiste la colonna '{col}' nella tabella selezionata."
        final_rows.append(filtered_row)

    return final_rows

def apply_order_by(rows, tokens):
    tokens_upper = [t.upper() for t in tokens]
    if "ORDER" not in tokens_upper or "BY" not in tokens_upper:
        return rows
    order_index = tokens_upper.index("ORDER")
    if len(tokens) < order_index + 3:
        return "Errore: Sintassi ORDER BY incompleta."
    col_order = tokens[order_index + 2]
    reverse_order = False
    if len(tokens) >= order_index + 4 and tokens[order_index + 3].upper() == "DESC":
        reverse_order = True

    try:
        return sorted(rows, key=lambda r: r[col_order], reverse=reverse_order)
    except KeyError:
        return f"Errore: La colonna '{col_order}' per l'ordinamento non esiste."


def apply_group_by(rows, tokens):
    tokens_upper = [t.upper() for t in tokens]
    if "GROUP" not in tokens_upper or "BY" not in tokens_upper:
        return rows

    group_index = tokens_upper.index("GROUP")
    end_group_index = len(tokens)
    for next_kw in ["HAVING", "ORDER"]:
        if next_kw in tokens_upper:
            kw_idx = tokens_upper.index(next_kw)
            if kw_idx > group_index:
                end_group_index = min(end_group_index, kw_idx)

    group_cols_raw = " ".join(tokens[group_index + 2: end_group_index])
    group_cols = [c.strip(", ") for c in group_cols_raw.replace(",", " ").split() if c.strip(", ")]

    if not group_cols:
        return "Errore: Sintassi GROUP BY incompleta."

    grouped_rows = []
    seen_keys = set()

    for row in rows:
        for col in group_cols:
            if col not in row:
                return f"Errore: La colonna '{col}' per il GROUP BY non esiste."

        key = tuple(row[col] for col in group_cols)
        if key not in seen_keys:
            seen_keys.add(key)
            grouped_rows.append(row)

    return grouped_rows


def apply_where(rows, tokens):
    tokens_upper = [t.upper() for t in tokens]
    if "WHERE" not in tokens_upper:
        return rows

    where_index = tokens_upper.index("WHERE")
    if len(tokens) < where_index + 4:
        return "Errore: Sintassi della clausola WHERE incompleta."

    col_where = tokens[where_index + 1]
    op_where = tokens[where_index + 2]
    val_where = tokens[where_index + 3]

    try:
        val_where = int(val_where)
    except ValueError:
        val_where = val_where.strip("'\"")

    nuove_righe = []
    for row in rows:
        if col_where not in row:
            return f"Errore: La colonna '{col_where}' non esiste nella tabella."

        cell_value = row[col_where]
        match = False
        if op_where == "==" or op_where == "=":
            match = (cell_value == val_where)
        elif op_where == ">":
            match = (cell_value > val_where)
        elif op_where == "<":
            match = (cell_value < val_where)
        elif op_where == ">=":
            match = (cell_value >= val_where)
        elif op_where == "<=":
            match = (cell_value <= val_where)

        if match:
            nuove_righe.append(row)

    return nuove_righe

# ------------------------ AGGREGATION FUNCTION ------------------ #

def apply_aggregate_function(rows, columns_requested, tokens):
    col_req_upper = columns_requested.strip().upper()
    tokens_upper = [t.upper() for t in tokens]

    has_group_by = "GROUP" in tokens_upper and "BY" in tokens_upper

    # CASE 1: AGGREGATION WITH GROUP BY
    if has_group_by:
        group_index = tokens_upper.index("GROUP")
        end_group_index = len(tokens)
        for next_kw in ["HAVING", "ORDER"]:
            if next_kw in tokens_upper:
                kw_idx = tokens_upper.index(next_kw)
                if kw_idx > group_index:
                    end_group_index = min(end_group_index, kw_idx)

        # extract group by column's
        group_cols_raw = " ".join(tokens[group_index + 2: end_group_index])
        group_cols = [c.strip(", ") for c in group_cols_raw.replace(",", " ").split() if c.strip(", ")]

        if not group_cols:
            return "Errore: Specifica almeno una colonna dopo GROUP BY."

        #check which aggregation function has been required
        func_name = None
        if "MIN(" in col_req_upper:
            func_name = "MIN"
        elif "MAX(" in col_req_upper:
            func_name = "MAX"
        elif "COUNT(" in col_req_upper:
            func_name = "COUNT"
        elif "SUM(" in col_req_upper:
            func_name = "SUM"
        elif "AVG(" in col_req_upper:
            func_name = "AVG"

        if func_name:
            start_idx = columns_requested.find("(")
            end_idx = columns_requested.find(")")
            col_agg = columns_requested[start_idx + 1: end_idx].strip() if start_idx != -1 and end_idx != -1 else ""

            agg_key_name = ""
            for col in columns_requested.split(','):
                if func_name in col.upper():
                    agg_key_name = col.strip()
                    break
            if not agg_key_name:
                agg_key_name = f"{func_name}({col_agg})"

            groups = {}
            for row in rows:
                for col in group_cols:
                    if col not in row:
                        return f"Errore: La colonna '{col}' non esiste."
                key = tuple(row[col] for col in group_cols)
                if key not in groups:
                    groups[key] = []
                groups[key].append(row)

            result_rows = []
            for key_tuple, group_rows in groups.items():
                if func_name == "COUNT":
                    agg_val = len(group_rows)
                elif func_name == "SUM":
                    value = [r[col_agg] for r in group_rows if col_agg in r and isinstance(r[col_agg], (int, float))]
                    agg_val = sum(value) if value else 0
                elif func_name == "AVG":
                    value = [r[col_agg] for r in group_rows if col_agg in r and isinstance(r[col_agg], (int, float))]
                    agg_val = sum(value) / len(value) if value else 0.0
                else:
                    value = [r[col_agg] for r in group_rows if col_agg in r and isinstance(r[col_agg], (int, float))]
                    agg_val = min(value) if func_name == "MIN" and value else (
                        max(value) if func_name == "MAX" and value else 0)

                row_result = {}
                for i, col in enumerate(group_cols):
                    row_result[col] = key_tuple[i]

                row_result[agg_key_name] = agg_val

                result_rows.append(row_result)
            return result_rows

    # CASE 2: AGGREGATION WITHOUT GROUP BY
    if col_req_upper.startswith("COUNT"):
        return len(rows)
    elif col_req_upper.startswith("MIN(") or col_req_upper.startswith("MAX(") or col_req_upper.startswith(
            "SUM(") or col_req_upper.startswith("AVG("):
        if not rows:
            return 0
        start_idx = columns_requested.find("(")
        end_idx = columns_requested.find(")")
        if start_idx != -1 and end_idx != -1:
            col_name = columns_requested[start_idx + 1: end_idx].strip()
            value = [row[col_name] for row in rows if col_name in row and isinstance(row[col_name], (int, float))]
            if not value:
                return f"Errore: La colonna '{col_name}' non esiste o non è numerica."
            if col_req_upper.startswith("MIN"):
                return min(value)
            elif col_req_upper.startswith("MAX"):
                return max(value)
            elif col_req_upper.startswith("SUM"):
                return sum(value)
            elif col_req_upper.startswith("AVG"):
                return sum(value) / len(value) if value else 0
    return None


##### HAVING ON GROUP BY AND ORDER BY
def apply_having(rows, tokens):
    tokens_upper = [t.upper() for t in tokens]

    if "HAVING" not in tokens_upper:
        return rows

    having_index = tokens_upper.index("HAVING")
    if len(tokens) < having_index + 4:
        return "Errore: sintassi della clausola Having incompleta o errata"

    col_having = tokens[having_index + 1]
    op_having = tokens[having_index + 2]
    val_having = tokens[having_index + 3]

    try:
        val_having = int(val_having)
    except ValueError:
        val_having = val_having.strip("'\"")

    filtered_groups = []
    for row in rows:
        cell_value = None
        for k in row:
            if k.upper() == col_having.upper():
                cell_value = row[k]
                break

        if cell_value is None:
            return f"Errore: La colonna o funzione '{col_having}' non è disponibile per il filtro HAVING."

        match = False
        if op_having == "==" or op_having == "=":
            match = (cell_value == val_having)
        elif op_having == ">":
            match = (cell_value > val_having)
        elif op_having == "<":
            match = (cell_value < val_having)
        elif op_having == ">=":
            match = (cell_value >= val_having)
        elif op_having == "<=":
            match = (cell_value <= val_having)

        if match:
            filtered_groups.append(row)

    return filtered_groups

#--------------------------------------------------------------------------#
###### JOIN OPERATION ###############

def apply_join(db, rows_t1, tokens):
    tokens_upper = [t.upper() for t in tokens]

    if "JOIN" not in tokens_upper:
        return rows_t1

    join_idx = tokens_upper.index("JOIN")
    on_idx = tokens_upper.index("ON") if "ON" in tokens_upper else -1

    if on_idx == -1 or len(tokens) < on_idx + 4:
        return "Errore: Sintassi JOIN incompleta. Usa: SELECT ... FROM t1 JOIN t2 ON t1.col = t2.col"

    t2_name = tokens[join_idx + 1]
    t2 = db.get_table(t2_name)
    if not t2 or isinstance(t2, list):
        return f"Errore: La tabella '{t2_name}' da unire non esiste."

    #extract the ON condition
    condition_left = tokens[on_idx + 1]
    operator = tokens[on_idx + 2]
    condition_right = tokens[on_idx + 3]

    col_t1 = condition_left.split(".")[-1]
    col_t2 = condition_right.split(".")[-1]

    #execute the inner join
    joined_rows = []
    for r1 in rows_t1:
        for r2 in t2.rows:
            if r1.get(col_t1) == r2.get(col_t2):
                #merge of collection
                merged_row = {}
                for k, v in r1.items():
                    supposed_key1 = f"{tokens[join_idx - 1]}.{k}"  # es. studenti.name
                    merged_row[supposed_key1] = v
                    merged_row[k] = v
                for k, v in r2.items():
                    supposed_key2 = f"{t2_name}.{k}"
                    merged_row[supposed_key2] = v
                    if k not in merged_row:
                        merged_row[k] = v

                joined_rows.append(merged_row)

    return joined_rows

#--------------------------------------------------------------------------#

def execute_query(db_name, query):
    cleaned_query = query.strip().rstrip(";")
    tokens = cleaned_query.split() #split the query with the space between words
    tokens_upper = [t.upper() for t in tokens]

    if len(tokens) >= 4 and tokens_upper[0] == "SELECT" and "FROM" in tokens_upper:
        from_index = tokens_upper.index("FROM")
        columns_requested_raw = " ".join(tokens[1:from_index])
        if len(tokens) > from_index + 1:
            table_name = tokens[from_index + 1]
        else:
            return "Errore: Specifica il nome della tabella dopo FROM."

        #find table in db and extract the rows
        table = db_name.get_table(table_name)
        rows = table.rows

        #apply join if is necessary
        rows = apply_join(db_name, rows, tokens)
        if isinstance(rows, str):
            return rows

        #apply where condition
        rows = apply_where(rows, tokens)
        if isinstance(rows, str):
            return rows

        #apply aggregation function
        agg_result = apply_aggregate_function(rows, columns_requested_raw, tokens)
        if agg_result is not None:
            if isinstance(agg_result, str):
                return agg_result
            rows = agg_result
        else:
            rows = apply_group_by(rows, tokens)
            if isinstance(rows, str):
                return rows
            rows = apply_projection(rows, columns_requested_raw)
            if isinstance(rows, str):
                return rows

        rows = apply_having(rows, tokens)
        if isinstance(rows, str):
            return rows

        #apply order by
        rows = apply_order_by(rows, tokens)
        if isinstance(rows, str):
            return rows

        #compute the final answer of the query
        result = apply_projection(rows, columns_requested_raw)
        return result

    else:
        return "Errore: sintassi non riconosciuta. Prova con: SELECT * FROM nome_tabella"


#---------------------- DEBUG -----------------#
my_db = Database("scuola_db")

tabella_studenti = Table("studenti")
tabella_studenti.add_column(Column("id", int))
tabella_studenti.add_column(Column("name", str))
tabella_studenti.add_column(Column("age", int))
tabella_studenti.add_column(Column("gender", str))

tabella_studenti.add_row({"id": 1, "name": "Milena", "age": 20, "gender": "F"})
tabella_studenti.add_row({"id": 2, "name": "Bob", "age": 24, "gender":"M"})
tabella_studenti.add_row({"id": 3, "name": "Charlie", "age": 22,"gender":"M"})
tabella_studenti.add_row({"id": 4, "name": "Diana", "age": 22, "gender": "F"})
tabella_studenti.add_row({"id": 5, "name": "Pippo", "age": 90, "gender": "M"})
tabella_studenti.add_row({"id": 6, "name": "Carla", "age": 16, "gender": "F"})
tabella_studenti.add_row({"id": 7, "name": "Pluto", "age": 34, "gender": "M"})
tabella_studenti.add_row({"id": 8, "name": "Millie", "age": 45, "gender": "F"})
tabella_studenti.add_row({"id": 9, "name": "Caterina", "age": 67, "gender": "M"})

my_db.add_table(tabella_studenti)

tabella_voti = Table("voti")
tabella_voti.add_column(Column("studente", int))
tabella_voti.add_column(Column("materia", str))
tabella_voti.add_column(Column("voto", int))

tabella_voti.add_row({"studente_id": 1, "materia": "Matematica", "voto": 30})
tabella_voti.add_row({"studente_id": 2, "materia": "Matematica", "voto": 22})
tabella_voti.add_row({"studente_id": 3, "materia": "Storia", "voto": 25})
tabella_voti.add_row({"studente_id": 4, "materia": "Storia", "voto": 30})

my_db.add_table(tabella_voti)

# ---------------- PROMPT -------------------------------#
if __name__ == "__main__":
    print("=" * 60)
    print(f"Benvenuto nel gestore di Database Relazionale: '{my_db.name}'")
    print("=" * 60)

    while True:
        print("\n--- MENU PRINCIPALE ---")
        print("1) Esegui una query SQL (SELECT)")
        print("2) Crea una nuova tabella")
        print("3) Inserisci dati in una tabella")
        print("4) Mostra stato del Database")
        print("5) Esci")

        user_input = input("\nScegli un'opzione (1-5): ").strip()

        if user_input == "1":
            print("\n--- SCHEMA DISPONIBILE ---")
            for name_tab, tab_obj in my_db.tables.items():
                column_name = ", ".join([col.name for col in tab_obj.columns])
                print(f"  {name_tab}: Colonne{{{column_name}}}")
            print("-" * 30)

            user_query = input("\nInserisci la query SQL: ").strip()
            if user_query:
                result = execute_query(my_db, user_query)
                print("\nRisultato:")
                print(result)

        elif user_input == "2":
            create_new_table(my_db)

        elif user_input == "3":
            insert_data(my_db)

        elif user_input == "4":

            print(f"\nStato attuale:")
            print(my_db)
            for name_table, tab_obj in my_db.tables.items():
                print(f"  - {tab_obj}")
                print(f"    Righe presenti: {tab_obj.rows}")

        elif user_input == "5":
            print("\nChiusura del programma. Arrivederci!")
            break

        else:
            print("\nScelta non valida. Inserisci un numero compreso tra 1 e 5.")