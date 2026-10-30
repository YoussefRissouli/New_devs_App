

## Fixes included

### Revenue came from fallback data

The database pool used settings that were not configured, so the dashboard query could fail. The old code then returned hard-coded revenue figures.

The pool now uses the configured database URL and a reusable async session. The fallback figures were removed, so the dashboard reads reservations from PostgreSQL.

### Cached revenue could cross client boundaries

The Redis cache key used only the property ID. `prop-001` exists for both clients, so one client could receive the other client's cached result.

Revenue cache entries now include the tenant ID, property ID, year, and month.

### The property selector exposed other clients' properties

The dashboard selector used a fixed list containing properties from both clients.

It now loads property IDs and names from a server endpoint filtered by the authenticated tenant.

### Monthly revenue did not use local month boundaries

The dashboard called its report monthly, but the query summed all reservations for a property. It also ignored the property's timezone.

The dashboard now sends a report month. The backend reads the property's timezone and filters reservations from the start of that local month to the start of the next one.

### Revenue was converted through floating-point numbers

The API converted money to a floating-point value, and the browser rounded it again. That can introduce small display differences.

Totals now remain `Decimal` values until the final half-up rounding step. The API sends the final amount as text, and the browser formats that text without another numeric conversion.

## Quick checks

Use March 2024 when checking the supplied seed data.

| Account | Property | Expected result |
| --- | --- | --- |
| Sunset Properties | Beach House Alpha | USD 2,250.00 and 4 bookings |
| Sunset Properties | Country Villa Estate | USD 6,100.50 and 2 bookings |
| Ocean Rentals | Mountain Lodge Beta | USD 0.00 and 0 bookings |
| Ocean Rentals | Lakeside Cottage | USD 1,776.50 and 4 bookings |
| Ocean Rentals | Urban Loft Modern | USD 3,256.00 and 3 bookings |

To verify tenant isolation, load `prop-001` for March 2024 as Sunset, then sign in as Ocean and load the same property ID. Sunset should receive USD 2,250.00. Ocean should receive USD 0.00.


## Notes

`NOTES.md` contains a short explanation of the revenue, tenant isolation, timezone, and precision fixes, along with steps for demonstrating each one.
