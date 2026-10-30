from backend.db import decisions_col, audit_trail_col, dlq_col

n1 = decisions_col.delete_many({}).deleted_count
n2 = audit_trail_col.delete_many({}).deleted_count
n3 = dlq_col.delete_many({}).deleted_count

print(f"decisions supprimees      : {n1}")
print(f"audit_trail supprimees    : {n2}")
print(f"dlq supprimees             : {n3}")
print("Base nettoyee. Les comptes recruteurs restent intacts.")
