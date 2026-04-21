f = open(r'C:\Users\flori\bigdogg_app\lib\screens\invoices_screen.dart', 'r', encoding='utf-8')
content = f.read()
f.close()

# 1. Add http and shared_preferences imports
if "import 'package:http/http.dart'" not in content:
    content = content.replace(
        "import 'package:flutter/material.dart';",
        "import 'dart:convert';\nimport 'package:flutter/material.dart';\nimport 'package:http/http.dart' as http;\nimport 'package:shared_preferences/shared_preferences.dart';"
    )

# 2. Add api_config import
if "api_config.dart" not in content:
    content = content.replace(
        "import '../theme.dart';",
        "import '../theme.dart';\nimport '../services/api_config.dart';"
    )

# 3. Add _fetchProjects helper before _showCreateInvoice
fetch_projects = '''
  Future<List<dynamic>> _fetchProjects() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final token = prefs.getString('access_token');
      final r = await http.get(
        Uri.parse('\${ApiConfig.baseUrl}/api/v1/projects/'),
        headers: {'Authorization': 'Bearer \$token'},
      );
      if (r.statusCode == 200) return jsonDecode(r.body)['projects'] ?? [];
    } catch (_) {}
    return [];
  }

'''
if '_fetchProjects' not in content:
    content = content.replace(
        '  void _showCreateInvoice(bool isNl) async {',
        fetch_projects + '  void _showCreateInvoice(bool isNl) async {'
    )

# 4. Fetch projects in _showCreateInvoice and add projectId variable
old_create = '''  void _showCreateInvoice(bool isNl) async {
    final clientsResult = await ClientsService.getClients();
    final productsResult = await ProductsService.getProducts();
    if (!clientsResult['success'] || !productsResult['success']) return;
    final clients = clientsResult['clients'] as List;
    final products = productsResult['products'] as List;
    if (!mounted) return;

    String? selectedClientId;
    List<Map<String, dynamic>> lines = [];'''

new_create = '''  void _showCreateInvoice(bool isNl) async {
    final clientsResult = await ClientsService.getClients();
    final productsResult = await ProductsService.getProducts();
    final projects = await _fetchProjects();
    if (!clientsResult['success'] || !productsResult['success']) return;
    final clients = clientsResult['clients'] as List;
    final products = productsResult['products'] as List;
    if (!mounted) return;

    String? selectedClientId;
    String? selectedProjectId;
    List<Map<String, dynamic>> lines = [];'''

content = content.replace(old_create, new_create)

# 5. Add project dropdown after the client dropdown in the dialog
old_client_dropdown = '''                DropdownButtonFormField<String>(
                  value: selectedClientId,
                  decoration:
                      InputDecoration(labelText: isNl ? 'Klant' : 'Client'),
                  items: clients
                      .map((c) => DropdownMenuItem<String>(
                            value: c['id'] as String,
                            child: Text(
                                c['company_name'] ?? c['contact_name']),
                          ))
                      .toList(),
                  onChanged: (val) =>
                      setDialogState(() => selectedClientId = val),
                ),
                const SizedBox(height: 16),'''

new_client_dropdown = '''                DropdownButtonFormField<String>(
                  value: selectedClientId,
                  decoration:
                      InputDecoration(labelText: isNl ? 'Klant' : 'Client'),
                  items: clients
                      .map((c) => DropdownMenuItem<String>(
                            value: c['id'] as String,
                            child: Text(
                                c['company_name'] ?? c['contact_name']),
                          ))
                      .toList(),
                  onChanged: (val) =>
                      setDialogState(() => selectedClientId = val),
                ),
                if (projects.isNotEmpty) ...[
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String?>(
                    value: selectedProjectId,
                    decoration: InputDecoration(
                        labelText: isNl ? 'Project (optioneel)' : 'Project (optional)'),
                    items: [
                      DropdownMenuItem<String?>(
                          value: null,
                          child: Text(isNl ? 'Geen project' : 'No project')),
                      ...projects.map((p) => DropdownMenuItem<String?>(
                            value: p['id'] as String,
                            child: Row(children: [
                              Container(
                                width: 10, height: 10,
                                decoration: BoxDecoration(
                                  color: Color(int.parse((p['color'] ?? '#1B3A4B').replaceFirst('#', '0xFF'))),
                                  shape: BoxShape.circle,
                                ),
                              ),
                              const SizedBox(width: 8),
                              Text(p['name'] ?? ''),
                            ]),
                          )),
                    ],
                    onChanged: (val) => setDialogState(() => selectedProjectId = val),
                  ),
                ],
                const SizedBox(height: 16),'''

content = content.replace(old_client_dropdown, new_client_dropdown)

# 6. Pass project_id when creating invoice
old_create_call = '''                      final result = await InvoicesService.createInvoice(
                          clientId: selectedClientId!, lines: lines);'''

new_create_call = '''                      final result = await InvoicesService.createInvoice(
                          clientId: selectedClientId!, lines: lines,
                          projectId: selectedProjectId);'''

content = content.replace(old_create_call, new_create_call)

f = open(r'C:\Users\flori\bigdogg_app\lib\screens\invoices_screen.dart', 'w', encoding='utf-8')
f.write(content)
f.close()

# Verify
c = open(r'C:\Users\flori\bigdogg_app\lib\screens\invoices_screen.dart').read()
print('_fetchProjects added:', '_fetchProjects' in c)
print('selectedProjectId added:', 'selectedProjectId' in c)
print('project dropdown added:', 'Geen project' in c or 'No project' in c)