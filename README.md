# fantasy-footballer

Fantasy Football Platform to easily interact and understand historical data.

High-level documentation has yet to be written
since the project is still in a period of rapid change. 

**Documentation under construction...**

---

## Testing

1. Run pre commit
   1. `make run-pre-commit`
2. Manually test app locally (Note: Do not commit any changes in `resources` directory!)
   1. `make run-local`
   2. Manual Testing
   3. Click `Shutdown` on Admin page
3. Run app container
   1. `make build`
   2. `make up`
   3. Manual Testing
   4. Exit docker with ^C
   5. `make down`
