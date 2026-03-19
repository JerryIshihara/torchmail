# TorchMail Architecture Diagrams

This directory contains Mermaid diagrams that visualize the TorchMail product scope and architecture.

## Available Diagrams

### 1. Complete Product Scope (`torchmail-product-scope.mmd`)
**Complexity**: High
**Purpose**: Comprehensive view of entire product ecosystem
**Shows**:
- All 7 epics with their components
- User journeys and interactions
- Data flows between systems
- External integrations
- Success metrics dashboard

**Best for**: Product planning, stakeholder presentations, architectural reviews

### 2. Simplified Product Scope (`torchmail-simple-scope.mmd`)
**Complexity**: Medium
**Purpose**: High-level product overview
**Shows**:
- Core user types and their benefits
- 7 major epics with key features
- Business outcomes and external systems
- Success metrics

**Best for**: Investor pitches, team onboarding, marketing materials

### 3. Core Architecture (`torchmail-core-architecture.mmd`)
**Complexity**: Technical
**Purpose**: Technical architecture visualization
**Shows**:
- Microservices architecture
- Data stores and external services
- Infrastructure components
- Data flow between services

**Best for**: Engineering planning, system design discussions, documentation

## How to Use These Diagrams

### Viewing the Diagrams
1. **Online Mermaid Editors**:
   - [Mermaid Live Editor](https://mermaid.live/)
   - [Mermaid Chart](https://www.mermaidchart.com/)
   - Copy the `.mmd` content into any Mermaid-compatible editor

2. **VS Code**:
   - Install "Markdown Preview Mermaid Support" extension
   - Open the `.mmd` file and preview

3. **GitHub/GitLab**:
   - Mermaid is natively supported in Markdown
   - Can be embedded in documentation

### Embedding in Documentation
```markdown
## Architecture Diagram

```mermaid
<!-- Copy content from .mmd file here -->
```

### Customizing Diagrams
1. Open the `.mmd` file in a text editor
2. Modify the Mermaid syntax as needed
3. Test in a Mermaid editor
4. Update and commit changes

## Diagram Key

### Color Coding
- **Blue**: Users and frontend components
- **Purple**: Product epics and features
- **Green**: Data stores and APIs
- **Orange**: Business and monetization
- **Pink**: External systems
- **Light Green**: Success metrics

### Shapes
- **Rectangle**: Components/services
- **Rounded Rectangle**: Groups/containers
- **Circle**: Start/end points
- **Diamond**: Decision points
- **Arrow**: Data flow/dependencies

## Generating Images

### Using Mermaid CLI
```bash
# Install mermaid CLI
npm install -g @mermaid-js/mermaid-cli

# Generate PNG from Mermaid file
mmdc -i torchmail-product-scope.mmd -o diagram.png

# Generate SVG
mmdc -i torchmail-product-scope.mmd -o diagram.svg
```

### Using Docker
```bash
docker run --rm -v $(pwd):/data minlag/mermaid-cli \
  -i /data/torchmail-product-scope.mmd \
  -o /data/diagram.png
```

## Updating Diagrams

### When to Update
1. **New Features Added**: Update relevant epic diagrams
2. **Architecture Changes**: Update core architecture diagram
3. **User Flow Changes**: Update data flow sections
4. **External Integrations**: Update external services section

### Update Process
1. Make changes to the `.mmd` file
2. Test in Mermaid editor
3. Update any dependent documentation
4. Commit changes with clear message
5. Regenerate images if needed

## Related Documentation

- `epics-milestones.md` - Detailed epic descriptions
- `technical-design-epic1.md` - Technical specifications
- `implementation-roadmap.md` - Development timeline
- `../architecture/` - Detailed architecture documentation

## Tools & Resources

### Mermaid Documentation
- [Official Mermaid Docs](https://mermaid.js.org/)
- [Syntax Guide](https://mermaid.js.org/syntax/flowchart.html)
- [Live Editor](https://mermaid.live/)

### Diagram Tools
- [Draw.io](https://draw.io) - Alternative diagram tool
- [Excalidraw](https://excalidraw.com) - Hand-drawn style diagrams
- [Lucidchart](https://lucidchart.com) - Professional diagramming

### Version Control
- All diagrams are text-based for easy diffing
- Store generated images in `docs/images/` if needed
- Include diagram updates in relevant PR descriptions

## Contributing New Diagrams

1. Create new `.mmd` file with descriptive name
2. Follow existing color coding and styling
3. Add to this README with description
4. Test in Mermaid editor
5. Submit PR with diagram and documentation updates

## Troubleshooting

### Common Issues
1. **Syntax Errors**: Check Mermaid syntax in online editor
2. **Rendering Issues**: Ensure proper indentation and line breaks
3. **Size Problems**: Break large diagrams into smaller ones
4. **Color Conflicts**: Maintain consistent color scheme

### Getting Help
- Check [Mermaid GitHub Issues](https://github.com/mermaid-js/mermaid/issues)
- Ask in team chat for diagram reviews
- Reference existing diagrams for patterns

---

*Diagrams last updated: March 19, 2026*  
*Maintained by: Product & Engineering Teams*