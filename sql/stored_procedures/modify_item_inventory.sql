DROP FUNCTION modify_plr_item_inventory(
	player_id integer, item_name text, mod_amount integer
);
CREATE OR REPLACE FUNCTION modify_plr_item_inventory(
	player_id integer, item_name text, mod_amount integer
) RETURNS integer AS
$BODY$
DECLARE
    new_balance INTEGER;
BEGIN
    LOOP
      -- first try to update the key
      UPDATE inventories_owneditem
        SET quantity=quantity + mod_amount
        WHERE owner_id=player_id AND item_id ILIKE item_name
        RETURNING quantity INTO new_balance;
      IF found THEN
        RETURN new_balance;
      END IF;
      -- not there, so try to insert the key
      -- if someone else inserts the same key concurrently,
      -- we could get a unique-key failure
      BEGIN
        INSERT INTO inventories_owneditem (item_id,quantity,owner_id)
		      VALUES (item_name, mod_amount, player_id);
        RETURN mod_amount;
      EXCEPTION WHEN unique_violation THEN
          -- Do nothing, and loop to try the UPDATE again.
      END;
    END LOOP;
END;
$BODY$
LANGUAGE plpgsql VOLATILE NOT LEAKPROOF
COST 100;
