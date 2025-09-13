# WeQuo Authoring Version Control System

## Overview

The WeQuo Authoring System provides comprehensive version control for weekly briefs with git-backed storage, collaborative editing, approval workflows, and editorial notes. This system enables authors to track changes, manage reviews, and maintain a complete audit trail of document evolution.

## Features

### 🔄 Version Control

- **Git-backed storage** with full commit history
- **Branching and merging** support for collaborative editing
- **Automatic versioning** with semantic version numbers
- **Revert capabilities** to restore previous versions
- **Diff visualization** to compare document versions

### 👥 Collaborative Workflow

- **Draft → Review → Approved → Published** state management
- **Multi-reviewer approval system** with customizable requirements
- **Editorial comments and notes** with threading support
- **Review notifications** via email integration
- **Approval tracking** with detailed audit trails

### 🎯 Authoring Features

- **Template-based document creation** using WeQuo analytics
- **Real-time editing** with auto-save capabilities
- **Line-by-line commenting** for precise feedback
- **Version comparison** with side-by-side diff views
- **Document metadata** tracking and provenance

### 📊 Workflow Management

- **Dashboard overview** of all documents and their states
- **Pending review tracking** with overdue notifications
- **Workflow statistics** and performance metrics
- **User role management** for authors and reviewers
- **Configurable approval rules** and timeouts

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 WeQuo Authoring System                 │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────────────────────┐ │
│  │  Web Interface  │  │         API Endpoints           │ │
│  │  - Dashboard    │  │  - Documents CRUD               │ │
│  │  - Editor       │  │  - Version management           │ │
│  │  │  - History   │  │  - Review workflow              │ │
│  │  - Diff Viewer  │  │  - Comments & approvals         │ │
│  └─────────────────┘  └─────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐ │
│  │              Workflow Engine                        │ │
│  │  - State management (draft/review/approved)         │ │
│  │  - Approval coordination                            │ │
│  │  - Notification system                              │ │
│  │  - Review assignment & tracking                     │ │
│  └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐ │
│  │             Version Controller                      │ │
│  │  - Git repository management                        │ │
│  │  - Document versioning                              │ │
│  │  - Diff generation                                  │ │
│  │  - Metadata storage                                 │ │
│  └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│  ┌───────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ Git Repository│  │  Metadata   │  │  Notifications  │ │
│  │ - Documents   │  │  - Versions │  │  - Email alerts │ │
│  │ - Commit log  │  │  - Comments │  │  - Review reqs  │ │
│  │ - Branches    │  │  - Approvals│  │  - Status updates│ │
│  └───────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. Run the Demo

```bash
cd wequo
python scripts/run_authoring_demo.py
```

This creates sample documents and demonstrates all features.

### 2. Start the Web Application

```bash
python scripts/run_web_app.py
```

Then visit: http://localhost:5000/authoring

### 3. Create Your First Brief

1. Click "New Brief" in the authoring dashboard
2. Edit the auto-generated template with your content
3. Save and submit for review
4. Reviewers can approve/reject with comments
5. Approved briefs can be published

## API Reference

### Documents

#### List Documents

```http
GET /api/authoring/documents
```

#### Create Document

```http
POST /api/authoring/documents
Content-Type: application/json

{
  "title": "Weekly Brief - 2025-01-15",
  "package_date": "2025-01-15",
  "author": "author@example.com",
  "reviewers": ["reviewer1@example.com", "reviewer2@example.com"],
  "initial_content": "# Brief content...",
  "auto_submit": false
}
```

#### Get Document

```http
GET /api/authoring/documents/{document_id}
```

### Versions

#### Create New Version

```http
POST /api/authoring/documents/{document_id}/versions
Content-Type: application/json

{
  "content": "Updated brief content...",
  "author": "author@example.com",
  "commit_message": "Updated risk assessment",
  "auto_submit": false
}
```

#### Get Version History

```http
GET /api/authoring/documents/{document_id}/history
```

#### Get Version Diff

```http
GET /api/authoring/documents/{document_id}/diff?version_a={id1}&version_b={id2}
```

### Workflow

#### Submit for Review

```http
POST /api/authoring/documents/{document_id}/submit
Content-Type: application/json

{
  "version_id": "version-uuid",
  "author": "author@example.com"
}
```

#### Review Document

```http
POST /api/authoring/documents/{document_id}/review
Content-Type: application/json

{
  "version_id": "version-uuid",
  "reviewer": "reviewer@example.com",
  "status": "approved", // approved, rejected, changes_requested
  "comments": "Looks good! Minor formatting suggestions addressed.",
  "author_email": "author@example.com"
}
```

#### Publish Document

```http
POST /api/authoring/documents/{document_id}/publish
Content-Type: application/json

{
  "version_id": "version-uuid"
}
```

### Comments

#### Add Comment

```http
POST /api/authoring/documents/{document_id}/comments
Content-Type: application/json

{
  "version_id": "version-uuid",
  "author": "reviewer@example.com",
  "content": "Consider expanding this section with more data.",
  "line_number": 42,
  "thread_id": "optional-thread-uuid"
}
```

### Statistics

#### Get Workflow Stats

```http
GET /api/authoring/stats
```

Response:

```json
{
  "total_documents": 15,
  "pending_reviews": 3,
  "overdue_reviews": 1,
  "avg_review_time": 18.5,
  "by_state": {
    "draft": 5,
    "review": 3,
    "approved": 4,
    "published": 3
  },
  "recent_activity": [...]
}
```

#### Get Pending Reviews

```http
GET /api/authoring/pending-reviews/{reviewer_email}
```

## Configuration

### Environment Variables

```bash
# Email notifications (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@example.com
SMTP_PASSWORD=your-app-password

# Authoring workspace
AUTHORING_WORKSPACE=./authoring_workspace
```

### Workflow Settings

Configure workflow behavior via API:

```http
PUT /api/authoring/settings
Content-Type: application/json

{
  "auto_submit_for_review": false,
  "required_approvals": 2,
  "approval_timeout_days": 3,
  "auto_publish_when_approved": false,
  "notify_reviewers": true,
  "notify_authors": true
}
```

## Document States

| State         | Description                     | Transitions                               |
| ------------- | ------------------------------- | ----------------------------------------- |
| **Draft**     | Initial state, being edited     | → Review                                  |
| **Review**    | Submitted for reviewer approval | → Draft (changes requested)<br>→ Approved |
| **Approved**  | All reviewers have approved     | → Published<br>→ Draft (new edits)        |
| **Published** | Final published version         | → Archived                                |
| **Archived**  | No longer active                | -                                         |

## Git Integration

The system uses Git for robust version control:

### Repository Structure

```
authoring_workspace/
├── .git/                    # Git repository
├── documents/               # Brief documents (.md files)
│   ├── 2025-01-15_brief.md
│   └── 2025-01-22_brief.md
├── .wequo/
│   └── metadata/           # Document metadata (.json files)
│       ├── {doc-id-1}.json
│       └── {doc-id-2}.json
└── README.md
```

### Git Commands

Every document operation creates Git commits:

```bash
# View repository log
cd authoring_workspace
git log --oneline

# View specific document history
git log -- documents/2025-01-15_brief.md

# View changes in a commit
git show {commit-hash}

# Create backup
git bundle create backup.bundle --all
```

## Integration with WeQuo Pipeline

The authoring system integrates seamlessly with the WeQuo data pipeline:

1. **Template Generation**: New briefs are pre-filled with analytics from the latest data package
2. **Data References**: Briefs can reference specific data points and analytics
3. **Export Integration**: Published briefs can be exported using the existing export system
4. **Search Integration**: Published briefs are indexed for the search system

## Best Practices

### For Authors

- **Use meaningful commit messages** when saving versions
- **Submit for review early** to get feedback during development
- **Respond to comments promptly** to maintain workflow momentum
- **Use line-specific comments** for precise feedback requests

### For Reviewers

- **Review within the timeout period** (default: 3 days)
- **Provide specific, actionable feedback** in comments
- **Use "Changes Requested"** rather than "Rejected" when possible
- **Approve quickly** when content meets standards

### For Administrators

- **Monitor overdue reviews** and follow up with reviewers
- **Adjust approval requirements** based on document importance
- **Configure email notifications** for timely workflow updates
- **Regular repository backups** using Git bundles

## Troubleshooting

### Common Issues

#### Git Repository Errors

```bash
# Reinitialize if repository is corrupted
cd authoring_workspace
git init
git add .
git commit -m "Reinitialize repository"
```

#### Permission Issues

```bash
# Fix file permissions
chmod -R 755 authoring_workspace
```

#### Email Notifications Not Working

1. Check SMTP settings in environment variables
2. Verify SMTP credentials and app passwords
3. Test email configuration with simple SMTP client

#### Version History Missing

- Check that metadata files exist in `.wequo/metadata/`
- Verify Git repository integrity
- Restore from backup if necessary

### Performance Optimization

For large numbers of documents:

- Use shallow Git clones for backups
- Implement pagination in document listings
- Consider archiving old documents
- Monitor disk space usage

## Development

### Adding New Features

1. **Models**: Update `wequo/src/wequo/authoring/models.py`
2. **Controllers**: Modify `wequo/src/wequo/authoring/version_control.py`
3. **Workflow**: Extend `wequo/src/wequo/authoring/workflow.py`
4. **API**: Add endpoints in `wequo/src/wequo/authoring/api.py`
5. **UI**: Update `wequo/templates/authoring_dashboard.html`

### Testing

```bash
# Run the demo to test all features
python scripts/run_authoring_demo.py

# Create test documents via API
curl -X POST http://localhost:5000/api/authoring/documents \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Brief", "package_date": "2025-01-15", "author": "test@example.com"}'
```

## Security Considerations

- **Git repository access** should be restricted to authorized users
- **API endpoints** should implement proper authentication
- **Email credentials** should be stored securely
- **Document metadata** may contain sensitive information
- **Backup repositories** should be encrypted

## Future Enhancements

- **Real-time collaborative editing** with operational transforms
- **Advanced diff visualization** with semantic understanding
- **Integration with external review tools** (GitHub, GitLab)
- **Document templates** with conditional logic
- **Automated quality checks** using AI/ML
- **Advanced analytics** on writing patterns and review cycles
- **Mobile interface** for review and approval on-the-go

---

For more information, see the [main WeQuo documentation](README.md) or contact the development team.
