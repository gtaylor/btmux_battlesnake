DROP FUNCTION modify_plr_blueprint_inventory(
	player_id integer, unit_ref text, blueprint_type text, mod_amount integer
);
CREATE OR REPLACE FUNCTION modify_plr_blueprint_inventory(
	player_id integer, unit_ref text, blueprint_type text, mod_amount integer
) RETURNS integer AS
$BODY$
DECLARE
    new_balance INTEGER;
BEGIN
    LOOP
      -- first try to update the key
      UPDATE inventories_ownedunitblueprint
        SET quantity=quantity + mod_amount
        WHERE owner_id=player_id AND unit_id ILIKE unit_ref AND
          bp_type ILIKE blueprint_type
        RETURNING quantity INTO new_balance;
      IF found THEN
        RETURN new_balance;
      END IF;
      -- not there, so try to insert the key
      -- if someone else inserts the same key concurrently,
      -- we could get a unique-key failure
      BEGIN
        INSERT INTO inventories_ownedunitblueprint (
          unit_id,bp_type,quantity,owner_id
        ) VALUES (unit_ref, blueprint_type, mod_amount, player_id);
        RETURN mod_amount;
      EXCEPTION WHEN unique_violation THEN
          -- Do nothing, and loop to try the UPDATE again.
      END;
    END LOOP;
END;
$BODY$
LANGUAGE plpgsql VOLATILE NOT LEAKPROOF
COST 100;
