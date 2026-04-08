export const regionOptions = [
  "us-east-1",
  "us-east-2",
  "us-west-1",
  "us-west-2",
  "eu-west-1",
  "eu-west-2",
  "eu-central-1",
  "ap-south-1",
  "ap-southeast-1",
  "ap-northeast-1",
];

export const serviceCatalog = {
  EC2: {
    title: "Amazon EC2",
    summary: "Estimate compute runtime with service-aware operating system and pricing model filters.",
    defaultValues: {
      region: "us-east-1",
      duration_hours: 100,
      configuration: {
        instance_type: "t3.micro",
        operating_system: "Linux",
        pricing_model: "OnDemand",
      },
    },
    fields: [
      { name: "instance_type", label: "Instance Type", type: "text", placeholder: "t3.micro" },
      {
        name: "operating_system",
        label: "Operating System",
        type: "select",
        options: ["Linux", "Windows"],
      },
      {
        name: "pricing_model",
        label: "Pricing Model",
        type: "select",
        options: ["OnDemand", "Reserved", "Spot"],
      },
    ],
  },
  S3: {
    title: "Amazon S3",
    summary: "Estimate monthly storage costs prorated over the selected duration horizon.",
    defaultValues: {
      region: "us-east-1",
      duration_hours: 720,
      configuration: {
        storage_gb: 500,
        storage_class: "Standard",
      },
    },
    fields: [
      { name: "storage_gb", label: "Storage (GB)", type: "number", min: 1 },
      {
        name: "storage_class",
        label: "Storage Class",
        type: "select",
        options: ["Standard", "StandardIA", "IntelligentTiering", "OneZoneIA"],
      },
    ],
  },
  Lambda: {
    title: "AWS Lambda",
    summary: "Estimate request and compute charges using invocation volume, memory, and execution time.",
    defaultValues: {
      region: "us-east-1",
      duration_hours: 24,
      configuration: {
        request_count: 1000000,
        execution_duration_ms: 250,
        memory_size_mb: 512,
      },
    },
    fields: [
      { name: "request_count", label: "Request Count", type: "number", min: 1 },
      {
        name: "execution_duration_ms",
        label: "Execution Duration (ms)",
        type: "number",
        min: 1,
      },
      { name: "memory_size_mb", label: "Memory (MB)", type: "number", min: 128 },
    ],
  },
};

