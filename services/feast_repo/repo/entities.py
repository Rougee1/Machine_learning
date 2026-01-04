from feast import Entity

# Définition de l'entité principale "user"
user = Entity(
    name="user",
    join_keys=["user_id"],
    description="Utilisateur (client) de StreamFlow identifié par son user_id",
)

