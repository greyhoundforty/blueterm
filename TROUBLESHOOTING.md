# Troubleshooting

## Authentication Issues

### "IBMCLOUD_API_KEY environment variable is required"

Make sure you've set the API key:

```bash
export IBMCLOUD_API_KEY="your-api-key"
```

Or create a `.env` file:

```bash
echo "IBMCLOUD_API_KEY=your-api-key" > .env
```

### "Failed to authenticate with IBM Cloud"

- Verify your API key is correct
- Check your network connectivity
- Ensure your API key has not expired
- Verify your API key has the required IAM permissions

### "Failed to get account ID"

- The app automatically retrieves your account ID from the API key
- If this fails, check your API key permissions
- Ensure you have IAM Identity Services read permissions

## Region Issues

### "Failed to load regions"

- Check your IBM Cloud account has VPC enabled
- Verify API key has proper IAM permissions
- Check network connectivity to IBM Cloud
- Try setting a specific default region: `export BLUETERM_DEFAULT_REGION="us-south"`

### Only 6 regions showing instead of 11

- The app fetches all regions from the VPC API
- If only 6 show, check that your account has access to all regions
- Verify the VPC API is accessible from your network

## Resource Group Issues

### "No resource groups available"

- Code Engine requires a resource group to be selected
- Click the "Change" button next to Resource Group to select one
- Verify your account has resource groups created
- Check IAM permissions for Resource Manager API

### Resource groups not showing in selection

- Ensure resource groups are loaded (check status bar)
- Verify your API key has Resource Manager API permissions
- Check that your account has resource groups

## Code Engine Issues

### No projects showing

- Verify you have Code Engine projects in the selected region
- Check that the selected resource group contains Code Engine projects
- Ensure your API key has Code Engine API permissions
- Try switching to a different region

### Project counts showing as 0

- The app fetches counts for apps, jobs, builds, and secrets
- If counts are 0, verify the project actually has resources
- Check API permissions for Code Engine resources
- Network issues may prevent fetching counts

### "Failed to load project resources"

- Check network connectivity
- Verify API permissions for Code Engine resources
- Ensure the project ID is valid
- Try refreshing with `R`

## Instance Actions

### Instance actions fail

- Verify instance state allows the action (e.g., can't stop a stopped instance)
- Check IAM permissions for instance actions
- Wait for pending operations to complete
- Check the status bar for error messages

### "Cannot start instance in X state"

- Instances must be stopped to start
- Wait for current operations to complete
- Check instance status in the details view (`d`)

## UI Issues

### Table not updating

- Press `R` to manually refresh
- Check if auto-refresh is enabled (`a` to toggle)
- Verify network connectivity
- Check status bar for error messages

### Colors not displaying correctly

- Ensure your terminal supports 256 colors
- Try a different theme (`t` to cycle)
- Check terminal emulator color support

### Keyboard shortcuts not working

- Ensure the table has focus (click on it or navigate with j/k)
- Check that you're not in a modal or search mode
- Press `Esc` to exit any active modes

## Performance Issues

### Slow loading

- Check network connectivity to IBM Cloud
- Reduce auto-refresh interval
- Disable auto-refresh if not needed
- Code Engine project counts may take time to fetch

### High CPU usage

- Disable auto-refresh
- Reduce refresh interval
- Check for network timeouts causing retries

## Logging

Enable debug logging for more information:

```bash
export BLUETERM_DEBUG="true"
```

Logs are written to:
- `~/.blueterm/blueterm.log` (file)
- stderr (console)

View logs in real-time:

```bash
tail -f ~/.blueterm/blueterm.log
```

## Getting Help

If you continue to experience issues:

1. Check the logs: `tail -f ~/.blueterm/blueterm.log`
2. Verify your API key permissions
3. Test API access with `ibmcloud` CLI
4. Open an issue on GitHub with:
   - Error message
   - Log output
   - Steps to reproduce
   - Your environment (OS, Python version)
